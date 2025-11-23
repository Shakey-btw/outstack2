import os
import base64
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from pydantic import BaseModel
from dotenv import load_dotenv
import time

load_dotenv()

app = FastAPI(title="Outstack API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Vercel deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lemlist API configuration
LEMLIST_API_KEY = os.getenv("LEMLIST_API_KEY", "")
LEMLIST_BASE_URL = "https://api.lemlist.com/api"

if not LEMLIST_API_KEY:
    print("Warning: LEMLIST_API_KEY not set in environment variables")


def get_auth_header() -> str:
    """Generate Basic Auth header for lemlist API"""
    if not LEMLIST_API_KEY:
        raise HTTPException(status_code=500, detail="LEMLIST_API_KEY not configured")
    credentials = f":{LEMLIST_API_KEY}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


async def fetch_with_retry(
    client: httpx.AsyncClient,
    url: str,
    params: Dict[str, Any],
    headers: Dict[str, str],
    max_retries: int = 3,
    base_timeout: float = 60.0,
    retry_delay: float = 1.0,
    operation_name: str = "API call"
) -> Optional[httpx.Response]:
    """
    Fetch with retry logic and exponential backoff
    """
    for attempt in range(max_retries):
        try:
            timeout = base_timeout * (attempt + 1)  # Increase timeout with each retry
            response = await client.get(url, params=params, headers=headers, timeout=timeout)
            
            # Check for rate limiting (429)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", retry_delay * (2 ** attempt)))
                print(f"Rate limited (429) on {operation_name}, waiting {retry_after}s before retry {attempt + 1}/{max_retries}")
                await asyncio.sleep(retry_after)
                continue
            
            # Check for server errors (5xx) - retry these
            if response.status_code >= 500:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"Server error {response.status_code} on {operation_name}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    response.raise_for_status()
            
            return response
            
        except httpx.TimeoutException as e:
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                print(f"Timeout on {operation_name}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
            else:
                print(f"Timeout on {operation_name} after {max_retries} attempts")
                raise
        except httpx.HTTPStatusError as e:
            # Don't retry on 4xx errors (except 429 which is handled above)
            if e.response.status_code < 500:
                raise
            # Retry on 5xx errors
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                print(f"HTTP error {e.response.status_code} on {operation_name}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
            else:
                raise
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                print(f"Error on {operation_name}: {str(e)}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
            else:
                raise
    
    return None


class CampaignData(BaseModel):
    campaign_id: str
    campaign_name: str
    companies_count: int
    people_count: int
    people_engaged: int
    open_rate: float
    reply_rate: float
    campaign_status: str


class MailboxData(BaseModel):
    email: str
    status: str
    mailbox_id: Optional[str] = None
    campaigns: Optional[List[str]] = None  # Campaign names this email is used in


@app.get("/")
async def root():
    return {"message": "Hello from FastAPI"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/campaigns/dashboard", response_model=List[CampaignData])
async def get_campaigns_dashboard():
    """
    Fetch running campaigns from lemlist and calculate dashboard metrics
    """
    if not LEMLIST_API_KEY:
        raise HTTPException(status_code=500, detail="LEMLIST_API_KEY not configured")
    
    auth_header = get_auth_header()
    headers = {"Authorization": auth_header}
    
    start_time = time.time()
    try:
        async with httpx.AsyncClient() as client:
            # Step 1: Fetch all running campaigns (handle pagination)
            all_campaigns = []
            page = 0
            print(f"Starting campaigns dashboard fetch at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            while True:
                try:
                    response = await fetch_with_retry(
                        client,
                        f"{LEMLIST_BASE_URL}/campaigns",
                        params={"status": "running", "limit": 100, "offset": page * 100},
                        headers=headers,
                        base_timeout=60.0,
                        operation_name=f"fetching campaigns page {page}"
                    )
                    if response is None:
                        print(f"Failed to fetch campaigns page {page} after retries")
                        break
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    # Handle different response formats
                    if isinstance(data, list):
                        campaigns = data
                        all_campaigns.extend(campaigns)
                        # If response is a list, check if we got all campaigns
                        if len(campaigns) < 100:
                            break
                    elif isinstance(data, dict):
                        campaigns = data.get("campaigns", [])
                        if not campaigns:
                            break
                        all_campaigns.extend(campaigns)
                        pagination = data.get("pagination", {})
                        total_pages = pagination.get("totalPages", 1)
                        if page >= total_pages - 1:
                            break
                        # If we got fewer than 100 campaigns, we've reached the end
                        if len(campaigns) < 100:
                            break
                    else:
                        campaigns = []
                        break
                    
                    page += 1
                except httpx.HTTPStatusError as e:
                    error_detail = f"HTTP {e.response.status_code}: {e.response.text}"
                    raise HTTPException(status_code=500, detail=f"Error fetching campaigns: {error_detail}")
                except httpx.HTTPError as e:
                    raise HTTPException(status_code=500, detail=f"Error fetching campaigns: {str(e)}")
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
            
            # Step 2: For each campaign, fetch leads and stats
            dashboard_data = []
            
            print(f"Processing {len(all_campaigns)} campaigns...")
            
            # Helper function to process a single campaign
            async def process_campaign(campaign: Dict[str, Any], idx: int, total: int) -> Optional[CampaignData]:
                """Process a single campaign and return CampaignData or None if failed"""
                campaign_id = campaign.get("_id") if isinstance(campaign, dict) else getattr(campaign, "_id", None)
                campaign_name = campaign.get("name", "Unnamed Campaign") if isinstance(campaign, dict) else getattr(campaign, "name", "Unnamed Campaign")
                
                if not campaign_id:
                    print(f"[{idx}/{total}] Skipping campaign with no ID: {campaign_name}")
                    return None
                
                print(f"[{idx}/{total}] Processing campaign: {campaign_name} (ID: {campaign_id})")
                
                try:
                    # Fetch leads for this campaign
                    campaign_start_time = time.time()
                    try:
                        leads_response = await fetch_with_retry(
                            client,
                            f"{LEMLIST_BASE_URL}/campaigns/{campaign_id}/export/leads",
                            params={"state": "all", "format": "json"},
                            headers=headers,
                            base_timeout=90.0,
                            operation_name=f"fetching leads for {campaign_name}"
                        )
                        if leads_response is None:
                            print(f"[{idx}/{total}] Failed to fetch leads for {campaign_name} after retries, skipping campaign")
                            return None
                        
                        leads_response.raise_for_status()
                        leads_data = leads_response.json()
                    except httpx.TimeoutException:
                        print(f"[{idx}/{total}] Timeout fetching leads for {campaign_name} after retries, skipping campaign")
                        return None
                    except Exception as leads_error:
                        print(f"[{idx}/{total}] Error fetching leads for {campaign_name}: {str(leads_error)}")
                        import traceback
                        traceback.print_exc()
                        return None
                    
                    # Handle different response formats for leads
                    if isinstance(leads_data, list):
                        leads = leads_data
                    elif isinstance(leads_data, dict):
                        leads = leads_data.get("leads", []) or leads_data.get("data", [])
                    else:
                        print(f"[{idx}/{total}] Warning: Unexpected leads data format for {campaign_name}: {type(leads_data)}")
                        leads = []
                    
                    if not isinstance(leads, list):
                        print(f"[{idx}/{total}] Warning: Leads is not a list for {campaign_name}, got {type(leads)}")
                        leads = []
                    
                    # Filter out paused leads
                    active_leads = [
                        lead for lead in leads
                        if isinstance(lead, dict) and lead.get("stateSystem") != "paused" and lead.get("state") != "paused"
                    ]
                    
                    total_leads = len(active_leads)
                    print(f"[{idx}/{total}] Campaign {campaign_name}: {total_leads} active leads (out of {len(leads)} total)")
                    
                    # Check if there are any leads with "readyToSend" or "inProgress" status
                    has_active_leads = False
                    lead_states_found = set()
                    for lead in active_leads:
                        if isinstance(lead, dict):
                            state = lead.get("state", "")
                            state_system = lead.get("stateSystem", "")
                            lead_states_found.add(f"state:{state}, stateSystem:{state_system}")
                            # Check for readyToSend in state or stateSystem
                            if state == "readyToSend" or state_system == "readyToSend":
                                has_active_leads = True
                                break
                            # Check for inProgress in stateSystem
                            if state_system == "inProgress":
                                has_active_leads = True
                                break
                    
                    # Set campaign status: "ended" if no active leads AND there are leads in the campaign
                    # If there are no leads at all, consider it active (it's a running campaign)
                    campaign_status = "ended" if (not has_active_leads and len(active_leads) > 0) else "active"
                    
                    # Debug logging for campaign status
                    if campaign_status == "ended":
                        print(f"[{idx}/{total}] Campaign {campaign_name} marked as 'ended' with {len(active_leads)} active leads. Sample states: {list(lead_states_found)[:5]}")
                    
                    # Count unique companies (non-null, non-empty companyName)
                    unique_companies = set()
                    for lead in active_leads:
                        if isinstance(lead, dict):
                            company_name = lead.get("companyName") or lead.get("company")
                            if company_name and str(company_name).strip():
                                unique_companies.add(str(company_name).strip())
                    
                    companies_count = len(unique_companies)
                    
                    # Initialize default stats values
                    people_engaged = 0  # This will be nbLeadsreached
                    opens = 0
                    replies = 0
                    sent = 0
                    nb_leads_reached = 0
                    unique_opens_count = 0
                    unique_replies_count = 0
                    
                    # Fetch stats from activities endpoint
                    activities_errors = []
                    activities_start_time = time.time()
                    try:
                        # Helper function to fetch all pages of an activity type
                        async def fetch_activity_pages(activity_type: str, max_pages: int = 100):
                            """Fetch all pages of a specific activity type"""
                            all_activities = []
                            page = 0
                            errors = []
                            while page < max_pages:
                                try:
                                    response = await fetch_with_retry(
                                        client,
                                        f"{LEMLIST_BASE_URL}/activities",
                                        params={"campaignId": campaign_id, "type": activity_type, "offset": page * 100, "limit": 100},
                                        headers=headers,
                                        base_timeout=60.0,
                                        max_retries=2,
                                        operation_name=f"fetching {activity_type} page {page} for {campaign_name}"
                                    )
                                    if response is None:
                                        errors.append(f"Failed to fetch {activity_type} page {page}")
                                        break
                                    
                                    if response.status_code != 200:
                                        try:
                                            error_text = response.text[:100] if hasattr(response, 'text') else str(response.status_code)
                                        except:
                                            error_text = f"Status {response.status_code}"
                                        errors.append(f"HTTP {response.status_code} on {activity_type} page {page}: {error_text}")
                                        break
                                    
                                    data = response.json()
                                    if not isinstance(data, list):
                                        errors.append(f"Unexpected {activity_type} data format on page {page}: {type(data)}")
                                        break
                                    
                                    if len(data) == 0:
                                        break
                                    
                                    all_activities.extend(data)
                                    if len(data) < 100:
                                        break
                                    page += 1
                                except httpx.TimeoutException:
                                    errors.append(f"Timeout fetching {activity_type} page {page}")
                                    break
                                except Exception as e:
                                    errors.append(f"Error fetching {activity_type} page {page}: {str(e)}")
                                    break
                            return all_activities, errors
                        
                        # Fetch all activity types in parallel
                        sent_task = fetch_activity_pages("emailsSent")
                        opens_task = fetch_activity_pages("emailsOpened")
                        replies_task = fetch_activity_pages("emailsReplied")
                        clicks_task = fetch_activity_pages("emailsClicked")
                        
                        # Wait for all to complete
                        (all_sent, sent_errors), (all_opens, opens_errors), (all_replies, replies_errors), (all_clicks, clicks_errors) = await asyncio.gather(
                            sent_task, opens_task, replies_task, clicks_task, return_exceptions=False
                        )
                        
                        # Collect all errors
                        activities_errors.extend(sent_errors)
                        activities_errors.extend(opens_errors)
                        activities_errors.extend(replies_errors)
                        # Don't log clicks errors as they're not critical
                        
                        # All activity types are now fetched in parallel above
                        sent = len(all_sent)
                        opens = len(all_opens)
                        replies = len(all_replies)
                        
                        if activities_errors:
                            print(f"[{idx}/{total}] Warnings fetching activities for {campaign_name}: {len(activities_errors)} errors")
                        
                        # Calculate nbLeadsreached: unique leads who received emails (were sent to)
                        unique_leads_reached = set()
                        for activity in all_sent:
                            if isinstance(activity, dict) and "leadId" in activity:
                                unique_leads_reached.add(activity["leadId"])
                        nb_leads_reached = len(unique_leads_reached)
                        people_engaged = nb_leads_reached  # Use nbLeadsreached as people engaged
                        
                        # Count unique leads who opened (not total opens)
                        unique_opens_lead_ids = set()
                        for activity in all_opens:
                            if isinstance(activity, dict) and "leadId" in activity:
                                unique_opens_lead_ids.add(activity["leadId"])
                        unique_opens_count = len(unique_opens_lead_ids)
                        
                        # Count unique leads who replied (not total replies)
                        unique_replies_lead_ids = set()
                        for activity in all_replies:
                            if isinstance(activity, dict) and "leadId" in activity:
                                unique_replies_lead_ids.add(activity["leadId"])
                        unique_replies_count = len(unique_replies_lead_ids)
                        
                        # Log summary of activities fetched
                        activities_duration = time.time() - activities_start_time
                        campaign_duration = time.time() - campaign_start_time
                        print(f"[{idx}/{total}] Campaign {campaign_name} activities: {nb_leads_reached} reached, {unique_opens_count} opened, {unique_replies_count} replied (activities: {activities_duration:.1f}s, total: {campaign_duration:.1f}s)")
                        
                        if activities_errors:
                            print(f"[{idx}/{total}] Campaign {campaign_name} had {len(activities_errors)} activity fetch errors (but continuing with partial data)")
                        
                    except Exception as stats_error:
                        # Stats endpoint failed completely, use default values
                        print(f"[{idx}/{total}] ERROR: Could not fetch stats for campaign {campaign_name} ({campaign_id}): {str(stats_error)}")
                        import traceback
                        traceback.print_exc()
                        unique_opens_count = 0
                        unique_replies_count = 0
                        nb_leads_reached = 0
                        people_engaged = 0
                    
                    # Calculate rates based on nbLeadsreached (people engaged)
                    open_rate = (unique_opens_count / nb_leads_reached * 100) if nb_leads_reached > 0 else 0.0
                    reply_rate = (unique_replies_count / nb_leads_reached * 100) if nb_leads_reached > 0 else 0.0
                    
                    campaign_data = CampaignData(
                        campaign_id=str(campaign_id),
                        campaign_name=str(campaign_name),
                        companies_count=companies_count,
                        people_count=total_leads,
                        people_engaged=int(people_engaged),
                        open_rate=round(open_rate, 2),
                        reply_rate=round(reply_rate, 2),
                        campaign_status=campaign_status
                    )
                    campaign_total_duration = time.time() - campaign_start_time
                    print(f"[{idx}/{total}] ✓ Successfully processed {campaign_name}: {total_leads} leads, {companies_count} companies, {people_engaged} engaged, {open_rate}% open, {reply_rate}% reply (total: {campaign_total_duration:.1f}s)")
                    return campaign_data
                    
                except httpx.HTTPStatusError as e:
                    # Log error but continue with other campaigns
                    print(f"Error processing campaign {campaign_id} ({campaign_name}): HTTP {e.response.status_code}: {e.response.text}")
                    return None
                except httpx.HTTPError as e:
                    # Log error but continue with other campaigns
                    print(f"Error processing campaign {campaign_id} ({campaign_name}): {str(e)}")
                    return None
                except Exception as e:
                    # Log error but continue with other campaigns
                    print(f"Unexpected error processing campaign {campaign_id} ({campaign_name}): {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return None
            
            # Process campaigns in batches of 2 to increase parallelization (max 8 concurrent calls: 2 campaigns × 4 activity calls)
            batch_size = 2
            for batch_start in range(0, len(all_campaigns), batch_size):
                batch_end = min(batch_start + batch_size, len(all_campaigns))
                batch = all_campaigns[batch_start:batch_end]
                
                # Process batch in parallel
                batch_results = await asyncio.gather(
                    *[process_campaign(campaign, batch_start + i + 1, len(all_campaigns)) for i, campaign in enumerate(batch)],
                    return_exceptions=False
                )
                
                # Add successful results to dashboard_data
                for result in batch_results:
                    if result is not None:
                        dashboard_data.append(result)
            
            # Processing complete - batch processing handles all campaigns above
            
            total_duration = time.time() - start_time
            avg_campaign_time = total_duration / len(dashboard_data) if len(dashboard_data) > 0 else 0
            print(f"✓ Completed processing: {len(dashboard_data)}/{len(all_campaigns)} campaigns returned in {total_duration:.1f}s (avg {avg_campaign_time:.1f}s per campaign)")
            if len(dashboard_data) < len(all_campaigns):
                print(f"⚠ WARNING: {len(all_campaigns) - len(dashboard_data)} campaigns were skipped due to errors")
            print(f"📊 Performance: Total time {total_duration:.1f}s for {len(dashboard_data)} campaigns = {avg_campaign_time:.1f}s/campaign average")
            return dashboard_data
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Unexpected error in dashboard endpoint: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.get("/api/mailboxes", response_model=List[MailboxData])
async def get_mailboxes():
    """
    Get all mailboxes and their status (in use or not in running campaigns)
    """
    if not LEMLIST_API_KEY:
        raise HTTPException(status_code=500, detail="LEMLIST_API_KEY not configured")
    
    auth_header = get_auth_header()
    headers = {"Authorization": auth_header}
    
    try:
        async with httpx.AsyncClient() as client:
            # Step 1: Get team senders to get userId
            senders_resp = await client.get(
                f"{LEMLIST_BASE_URL}/team/senders",
                headers=headers,
                timeout=30.0
            )
            senders_resp.raise_for_status()
            senders_data = senders_resp.json()
            
            if not isinstance(senders_data, list) or len(senders_data) == 0:
                print("Warning: No team senders found or invalid format")
                return []
            
            # Get userId from first sender (assuming single user for now)
            userId = senders_data[0].get("userId")
            if not userId:
                print(f"Warning: No userId found in senders data: {senders_data}")
                return []
            
            print(f"Found userId: {userId}")
            
            # Step 2: Get all mailboxes for this user
            user_resp = await client.get(
                f"{LEMLIST_BASE_URL}/users/{userId}",
                headers=headers,
                timeout=30.0
            )
            user_resp.raise_for_status()
            user_data = user_resp.json()
            
            all_mailboxes = user_data.get("mailboxes", [])
            if not isinstance(all_mailboxes, list):
                print(f"Warning: Mailboxes is not a list. Got: {type(all_mailboxes)}")
                return []
            
            print(f"Found {len(all_mailboxes)} mailboxes for user {userId}")
            
            # Step 3: Get sender emails used in running campaigns
            # Get running campaigns with pagination
            all_running_campaigns = []
            page = 0
            while True:
                campaigns_resp = await client.get(
                    f"{LEMLIST_BASE_URL}/campaigns",
                    params={"status": "running", "limit": 100, "offset": page * 100},
                    headers=headers,
                    timeout=60.0
                )
                campaigns_resp.raise_for_status()
                campaigns_data = campaigns_resp.json()
                
                # Handle different response formats
                if isinstance(campaigns_data, list):
                    campaigns = campaigns_data
                elif isinstance(campaigns_data, dict):
                    campaigns = campaigns_data.get("campaigns", [])
                    pagination = campaigns_data.get("pagination", {})
                    total_pages = pagination.get("totalPages", 1)
                    if page >= total_pages - 1:
                        all_running_campaigns.extend(campaigns)
                        break
                else:
                    campaigns = []
                
                if not campaigns:
                    break
                
                all_running_campaigns.extend(campaigns)
                page += 1
                if len(campaigns) < 100:
                    break
            
            # Collect emails in use (only from campaigns with active leads)
            # Also collect all campaigns each email is in (for info popup)
            emails_in_use = set()
            email_to_campaigns: Dict[str, List[str]] = {}  # Map email to list of campaign names
            mailbox_id_to_emails: Dict[str, set] = {}  # Map mailbox_id to set of emails used in campaigns
            
            for campaign in all_running_campaigns:
                campaign_id = campaign.get("_id")
                campaign_name = campaign.get("name", "Unknown Campaign")
                if campaign_id:
                    try:
                        # Check if campaign has active leads (ready to send or in progress)
                        leads_response = await client.get(
                            f"{LEMLIST_BASE_URL}/campaigns/{campaign_id}/export/leads",
                            params={"state": "all", "format": "json"},
                            headers=headers,
                            timeout=60.0
                        )
                        if leads_response.status_code == 200:
                            leads_data = leads_response.json()
                            # Handle different response formats for leads
                            if isinstance(leads_data, list):
                                leads = leads_data
                            elif isinstance(leads_data, dict):
                                leads = leads_data.get("leads", []) or leads_data.get("data", [])
                            else:
                                leads = []
                            
                            # Filter out paused leads
                            active_leads = [
                                lead for lead in leads
                                if isinstance(lead, dict) and lead.get("stateSystem") != "paused" and lead.get("state") != "paused"
                            ]
                            
                            # Check if there are any leads with "readyToSend" or "inProgress" status
                            has_active_leads = False
                            for lead in active_leads:
                                if isinstance(lead, dict):
                                    state = lead.get("state", "")
                                    state_system = lead.get("stateSystem", "")
                                    # Check for readyToSend in state or stateSystem
                                    if state == "readyToSend" or state_system == "readyToSend":
                                        has_active_leads = True
                                        break
                                    # Check for inProgress in stateSystem
                                    if state_system == "inProgress":
                                        has_active_leads = True
                                        break
                            
                            # Get campaign details to check senders
                            campaign_detail_resp = await client.get(
                                f"{LEMLIST_BASE_URL}/campaigns/{campaign_id}",
                                headers=headers,
                                timeout=60.0
                            )
                            if campaign_detail_resp.status_code == 200:
                                campaign_detail = campaign_detail_resp.json()
                                if "senders" in campaign_detail:
                                    for sender in campaign_detail["senders"]:
                                        # Only count senders that have an email field (not type: 'api', 'linkedinVisit', etc.)
                                        email = sender.get("email")
                                        sender_mailbox_id = sender.get("sendUserMailboxId")
                                        if email and isinstance(email, str) and "@" in email:
                                            # Add to campaigns list for this email (for info popup)
                                            if email not in email_to_campaigns:
                                                email_to_campaigns[email] = []
                                            email_to_campaigns[email].append(campaign_name)
                                            
                                            # Track which mailbox_id uses which email
                                            if sender_mailbox_id:
                                                if sender_mailbox_id not in mailbox_id_to_emails:
                                                    mailbox_id_to_emails[sender_mailbox_id] = set()
                                                mailbox_id_to_emails[sender_mailbox_id].add(email)
                                            
                                            # Only count as "in use" if campaign has active leads
                                            if has_active_leads:
                                                emails_in_use.add(email)
                    except Exception as e:
                        print(f"Error processing campaign {campaign_id} ({campaign_name}): {str(e)}")
                        import traceback
                        traceback.print_exc()
                        continue
            
            # Also check all campaigns (not just running) to get complete campaign list for info popup
            all_campaigns = []
            page = 0
            while True:
                campaigns_resp = await client.get(
                    f"{LEMLIST_BASE_URL}/campaigns",
                    params={"limit": 100, "offset": page * 100},
                    headers=headers,
                    timeout=60.0
                )
                campaigns_resp.raise_for_status()
                campaigns_data = campaigns_resp.json()
                if isinstance(campaigns_data, list):
                    campaigns = campaigns_data
                elif isinstance(campaigns_data, dict):
                    campaigns = campaigns_data.get("campaigns", [])
                    pagination = campaigns_data.get("pagination", {})
                    total_pages = pagination.get("totalPages", 1)
                    if page >= total_pages - 1:
                        all_campaigns.extend(campaigns)
                        break
                else:
                    campaigns = []
                if not campaigns:
                    break
                all_campaigns.extend(campaigns)
                page += 1
                if len(campaigns) < 100:
                    break
            
            # Add campaigns from all campaigns (not just running) to the email_to_campaigns map
            for campaign in all_campaigns:
                campaign_id = campaign.get("_id")
                campaign_name = campaign.get("name", "Unknown Campaign")
                if campaign_id:
                    try:
                        campaign_detail_resp = await client.get(
                            f"{LEMLIST_BASE_URL}/campaigns/{campaign_id}",
                            headers=headers,
                            timeout=60.0
                        )
                        if campaign_detail_resp.status_code == 200:
                            campaign_detail = campaign_detail_resp.json()
                            if "senders" in campaign_detail:
                                for sender in campaign_detail["senders"]:
                                    email = sender.get("email")
                                    sender_mailbox_id = sender.get("sendUserMailboxId")
                                    if email and isinstance(email, str) and "@" in email:
                                        if email not in email_to_campaigns:
                                            email_to_campaigns[email] = []
                                        if campaign_name not in email_to_campaigns[email]:
                                            email_to_campaigns[email].append(campaign_name)
                                        
                                        # Track which mailbox_id uses which email (for all campaigns)
                                        if sender_mailbox_id:
                                            if sender_mailbox_id not in mailbox_id_to_emails:
                                                mailbox_id_to_emails[sender_mailbox_id] = set()
                                            mailbox_id_to_emails[sender_mailbox_id].add(email)
                    except Exception as e:
                        print(f"Error processing campaign {campaign_id} for email mapping: {str(e)}")
                        continue
            
            # Create a map of mailbox_id to the email actually used in campaigns
            mailbox_id_to_campaign_email: Dict[str, str] = {}
            for campaign in all_campaigns:
                campaign_id = campaign.get("_id")
                if campaign_id:
                    try:
                        campaign_detail_resp = await client.get(
                            f"{LEMLIST_BASE_URL}/campaigns/{campaign_id}",
                            headers=headers,
                            timeout=30.0
                        )
                        if campaign_detail_resp.status_code == 200:
                            campaign_detail = campaign_detail_resp.json()
                            if "senders" in campaign_detail:
                                for sender in campaign_detail["senders"]:
                                    sender_email = sender.get("email")
                                    sender_mailbox_id = sender.get("sendUserMailboxId")
                                    if sender_email and isinstance(sender_email, str) and "@" in sender_email and sender_mailbox_id:
                                        # Use the email from the campaign (actual email being used)
                                        mailbox_id_to_campaign_email[sender_mailbox_id] = sender_email
                    except Exception as e:
                        print(f"Error processing campaign {campaign_id} for email mapping: {str(e)}")
                        continue
            
            # Step 4: Build response with combined status
            mailbox_list = []
            skipped_mailboxes = 0
            for mailbox in all_mailboxes:
                mailbox_id = mailbox.get("_id", "")
                # Use the email from campaigns if available, otherwise use mailbox email
                email = mailbox_id_to_campaign_email.get(mailbox_id, mailbox.get("email", ""))
                if not email:
                    email = mailbox.get("email", "")
                
                if not email:
                    skipped_mailboxes += 1
                    print(f"Warning: Skipping mailbox {mailbox_id} - no email found. Mailbox data: {mailbox}")
                    continue
                
                if email:
                    # Check if email is in use - check all emails associated with this mailbox_id
                    mailbox_email = mailbox.get("email", "")
                    # Get all emails used by this mailbox_id in campaigns
                    campaign_emails = mailbox_id_to_emails.get(mailbox_id, set())
                    # Check if any of these emails are in use
                    is_in_use = (
                        email in emails_in_use or 
                        mailbox_email in emails_in_use or
                        any(campaign_email in emails_in_use for campaign_email in campaign_emails)
                    )
                    
                    lemwarm = mailbox.get("lemwarm", {})
                    is_warming_up = lemwarm.get("active", False) if isinstance(lemwarm, dict) else False
                    
                    # Debug logging for status determination
                    if email != mailbox_email:
                        print(f"Mailbox {mailbox_id}: Using campaign email '{email}' (mailbox email: '{mailbox_email}')")
                    
                    # Determine status based on both conditions
                    if is_warming_up and is_in_use:
                        status = "conflict"
                    elif is_in_use:
                        status = "in use"
                    elif is_warming_up:
                        status = "warming up"
                    else:
                        status = "stuck"
                    
                    # Debug logging for status
                    if status in ["stuck", "conflict"]:
                        print(f"Mailbox {email}: status={status}, is_in_use={is_in_use}, is_warming_up={is_warming_up}, campaigns={email_to_campaigns.get(email, [])}")
                    
                    # Get campaigns for this email (only for stuck/conflict statuses)
                    # Check both the mailbox email and campaign email
                    campaigns = None
                    if status in ["stuck", "conflict"]:
                        campaigns = email_to_campaigns.get(email, [])
                        # Also check mailbox email if different
                        mailbox_email = mailbox.get("email", "")
                        if mailbox_email != email and mailbox_email in email_to_campaigns:
                            if campaigns:
                                campaigns = list(set(campaigns + email_to_campaigns[mailbox_email]))
                            else:
                                campaigns = email_to_campaigns[mailbox_email]
                    
                    mailbox_list.append(MailboxData(
                        email=email,
                        status=status,
                        mailbox_id=mailbox_id,
                        campaigns=campaigns if campaigns else None
                    ))
            
            # Sort by status priority: stuck, conflict, in use, warming up
            status_order = {"stuck": 0, "conflict": 1, "in use": 2, "warming up": 3}
            mailbox_list.sort(key=lambda x: (status_order.get(x.status, 99), x.email))
            
            # Summary logging
            status_counts = {}
            for mb in mailbox_list:
                status_counts[mb.status] = status_counts.get(mb.status, 0) + 1
            
            print(f"Returning {len(mailbox_list)} mailboxes (skipped {skipped_mailboxes} without email)")
            print(f"Status breakdown: {status_counts}")
            print(f"Emails in use: {len(emails_in_use)} unique emails")
            return mailbox_list
            
    except httpx.HTTPStatusError as e:
        error_detail = f"HTTP {e.response.status_code}: {e.response.text}"
        raise HTTPException(status_code=500, detail=f"Error fetching mailboxes: {error_detail}")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error fetching mailboxes: {str(e)}")
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Unexpected error in mailboxes endpoint: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post("/api/mailboxes/{mailbox_id}/start-lemwarm")
async def start_lemwarm(mailbox_id: str):
    """
    Start lemwarm for a specific mailbox
    """
    if not LEMLIST_API_KEY:
        raise HTTPException(status_code=500, detail="LEMLIST_API_KEY not configured")
    
    auth_header = get_auth_header()
    headers = {"Authorization": auth_header}
    
    try:
        async with httpx.AsyncClient() as client:
            # Call lemlist API to start lemwarm
            response = await client.post(
                f"{LEMLIST_BASE_URL}/lemwarm/{mailbox_id}/start",
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            return {"success": True, "message": "Lemwarm started successfully"}
            
    except httpx.HTTPStatusError as e:
        error_detail = f"HTTP {e.response.status_code}: {e.response.text}"
        raise HTTPException(status_code=e.response.status_code, detail=f"Error starting lemwarm: {error_detail}")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error starting lemwarm: {str(e)}")
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Unexpected error starting lemwarm: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post("/api/mailboxes/{mailbox_id}/stop-lemwarm")
async def stop_lemwarm(mailbox_id: str):
    """
    Stop lemwarm for a specific mailbox
    """
    if not LEMLIST_API_KEY:
        raise HTTPException(status_code=500, detail="LEMLIST_API_KEY not configured")
    
    auth_header = get_auth_header()
    headers = {"Authorization": auth_header}
    
    try:
        async with httpx.AsyncClient() as client:
            # Call lemlist API to pause/stop lemwarm
            response = await client.post(
                f"{LEMLIST_BASE_URL}/lemwarm/{mailbox_id}/pause",
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            return {"success": True, "message": "Lemwarm stopped successfully"}
            
    except httpx.HTTPStatusError as e:
        error_detail = f"HTTP {e.response.status_code}: {e.response.text}"
        raise HTTPException(status_code=e.response.status_code, detail=f"Error stopping lemwarm: {error_detail}")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error stopping lemwarm: {str(e)}")
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Unexpected error stopping lemwarm: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post("/api/campaigns/{campaign_id}/set-inactive")
async def set_campaign_inactive(campaign_id: str):
    """
    Set a campaign as inactive (pause it)
    """
    if not LEMLIST_API_KEY:
        raise HTTPException(status_code=500, detail="LEMLIST_API_KEY not configured")
    
    auth_header = get_auth_header()
    headers = {"Authorization": auth_header}
    
    try:
        async with httpx.AsyncClient() as client:
            # Call lemlist API to pause the campaign
            response = await client.post(
                f"{LEMLIST_BASE_URL}/campaigns/{campaign_id}/pause",
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            return {"success": True, "message": "Campaign set to inactive successfully"}
            
    except httpx.HTTPStatusError as e:
        error_detail = f"HTTP {e.response.status_code}: {e.response.text}"
        raise HTTPException(status_code=e.response.status_code, detail=f"Error setting campaign inactive: {error_detail}")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Error setting campaign inactive: {str(e)}")
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Unexpected error setting campaign inactive: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Wrap the FastAPI app with Mangum for Vercel serverless functions
from mangum import Mangum
handler = Mangum(app, lifespan="off")

# Deployment version: 03c6935 - All FastAPI code in index.py to avoid import issues

