# API Rate Limit Analysis

## Lemlist API Rate Limits
According to Lemlist documentation, the rate limit is: **20 API requests per 2 seconds per API key**.

## Current API Call Patterns

### 1. Campaigns Dashboard Endpoint (`/api/campaigns/dashboard`)

#### Sequential Phase:
- **Campaigns List Fetching**: Sequential pagination
  - 1 call per page (typically 1-2 pages)
  - Rate: ~1 call per request (not parallel)

#### Per-Campaign Processing (Sequential):
For each campaign, the following calls are made:

1. **Leads Fetch**: 1 call
   - `GET /campaigns/{campaignId}/export/leads`
   - Sequential (one campaign at a time)

2. **Activities Fetch**: 4 calls in parallel (using `asyncio.gather`)
   - `GET /activities?type=emailsSent&campaignId={campaignId}`
   - `GET /activities?type=emailsOpened&campaignId={campaignId}`
   - `GET /activities?type=emailsReplied&campaignId={campaignId}`
   - `GET /activities?type=emailsClicked&campaignId={campaignId}`
   - **Each activity type can have pagination** (multiple pages per type)
   - **Maximum parallel calls per campaign: 4** (one per activity type, first page)
   - **Subsequent pages are sequential** within each activity type

#### Maximum Concurrent Calls in Campaigns Dashboard:
- **Per campaign**: 4 parallel calls (activities)
- **Campaigns are processed sequentially**, so maximum concurrent = 4 calls
- **However**: If activity pagination is needed, additional pages are fetched sequentially after the first page completes

**Worst-case scenario**: 
- 4 parallel calls (activities for one campaign)
- If each activity type needs 2 pages, that's 4 initial calls + 4 sequential follow-ups = 8 calls per campaign, but still max 4 concurrent

### 2. Mailboxes Endpoint (`/api/mailboxes`)

#### Initial Setup (Sequential):
1. `GET /team/senders` - 1 call
2. `GET /users/{userId}` - 1 call

#### Running Campaigns Fetch (Sequential):
3. `GET /campaigns?status=running` - Paginated, sequential (1 call per page)

#### Per Running Campaign Processing (Sequential):
For each running campaign:
4. `GET /campaigns/{campaignId}/export/leads` - 1 call per campaign
5. `GET /campaigns/{campaignId}` - 1 call per campaign
- **These are sequential** (not parallel)
- **Total: 2 calls per running campaign**

#### All Campaigns Fetch (Sequential):
6. `GET /campaigns` - Paginated, sequential (1 call per page)

#### Per All Campaign Processing (Sequential):
For each campaign (all campaigns, not just running):
7. `GET /campaigns/{campaignId}` - 1 call per campaign
- **Sequential processing**
- **Note**: This happens in two separate loops (lines 674-704 and 706-728)
- **Total: 2 calls per campaign (all campaigns)** - appears to be redundant fetching

#### Maximum Concurrent Calls in Mailboxes Endpoint:
- **Maximum concurrent: 1 call** (all processing is sequential)
- No parallelization in this endpoint
- **Total calls for mailboxes**: 1 (senders) + 1 (user) + N (running campaigns pages) + 2×R (running campaigns: leads + detail) + M (all campaigns pages) + 2×A (all campaigns: detail, fetched twice)
  - Where R = number of running campaigns, A = number of all campaigns
  - **Example**: If 10 running campaigns and 20 total campaigns = 1 + 1 + 1 + 20 + 1 + 40 = 64 calls total (but sequential)
  - **Note**: The all campaigns detail is fetched twice (appears redundant - could be optimized)

### 3. Combined Dashboard Load (Initial Page Load)

When the page loads, both endpoints are called:
1. Campaigns dashboard starts first
2. Mailboxes dashboard starts after 500ms delay (staggered)

**Maximum concurrent calls during initial load:**
- Campaigns: 4 parallel calls (activities)
- Mailboxes: 1 call (sequential)
- **Total maximum concurrent: 5 calls**

However, since mailboxes starts 500ms after campaigns, and campaigns processes sequentially, the actual overlap is minimal.

## Analysis Summary

### Current Maximum API Calls per 2-Second Window

**Campaigns Dashboard (worst case):**
- 4 parallel calls (activities for one campaign)
- If processing multiple campaigns quickly, but still sequential, so max 4 concurrent
- **Maximum: 4 calls per 2 seconds** (if activities complete quickly)

**Mailboxes Dashboard:**
- All sequential, so **maximum: 1 call per 2 seconds**

**Combined (if both run simultaneously):**
- **Maximum: 5 calls per 2 seconds** (4 from campaigns + 1 from mailboxes)

### Rate Limit Headroom

**Lemlist Rate Limit**: 20 requests per 2 seconds
**Current Maximum Usage**: ~5 requests per 2 seconds
**Available Headroom**: **~15 requests per 2 seconds (75% unused capacity)**

## Opportunities for Parallelization

### 1. Campaigns Dashboard
- **Current**: 4 parallel calls per campaign (activities)
- **Potential**: Could process multiple campaigns in parallel
  - If processing 5 campaigns in parallel, each with 4 activity calls = 20 calls
  - This would hit the rate limit exactly
  - **Recommendation**: Process 3-4 campaigns in parallel (12-16 calls) to leave buffer

### 2. Mailboxes Dashboard
- **Current**: All sequential
- **Potential**: Could parallelize campaign detail fetching
  - For running campaigns: Fetch leads + campaign detail in parallel (2 calls per campaign)
  - For all campaigns: Fetch campaign details in parallel (batch of 10-15 at a time)
  - **Recommendation**: Process campaigns in batches of 10-15 in parallel

### 3. Activity Pagination
- **Current**: Sequential pagination within each activity type
- **Potential**: Could fetch multiple pages in parallel (but this might not be worth it due to complexity)

## Recommendations

### Safe Parallelization Strategy

1. **Campaigns Dashboard**:
   - Process campaigns in batches of 3-4 campaigns in parallel
   - Each batch: 3-4 campaigns × 4 activity calls = 12-16 concurrent calls
   - Leaves 4-8 calls headroom for mailboxes and other operations
   - **Expected speedup**: 3-4x faster for campaigns processing

2. **Mailboxes Dashboard**:
   - Process running campaigns in batches of 10-15 in parallel
   - Each batch: 10-15 campaigns × 2 calls (leads + detail) = 20-30 calls
   - **Wait**: This would exceed the rate limit!
   - **Better**: Process in batches of 8-10 campaigns (16-20 calls, at the limit)
   - Or: Process leads and details sequentially but batch campaigns (10 campaigns × 1 call = 10 calls per batch)
   - **Expected speedup**: 8-10x faster for mailboxes processing

3. **Combined Strategy**:
   - When both dashboards load:
     - Campaigns: 3 campaigns in parallel (12 calls)
     - Mailboxes: Wait or use remaining capacity (8 calls)
     - **Total: 20 calls** (at the limit, but safe with proper error handling)

### Implementation Considerations

1. **Rate Limit Monitoring**: 
   - Check `X-RateLimit-Remaining` header in responses
   - Implement dynamic throttling if remaining < 5

2. **Error Handling**:
   - Current retry logic handles 429 errors well
   - With parallelization, need to handle partial failures gracefully

3. **Staggered Loading**:
   - Current 500ms delay between dashboards is good
   - Could reduce to 200ms with parallelization

## Conclusion

**Current State**: Using ~25% of rate limit capacity (5/20 calls per 2 seconds)
**Potential**: Can safely increase to ~80-90% (16-18 calls per 2 seconds)
**Expected Speedup**: 3-10x faster dashboard loading
**Risk**: Low (with proper error handling and monitoring)

