# Outstack

Full-stack application with FastAPI backend and Next.js frontend.

## Project Structure

```
outstack2/
├── backend/          # FastAPI backend
│   ├── main.py
│   └── requirements.txt
└── frontend/         # Next.js frontend
    ├── app/
    ├── components/
    ├── lib/
    └── package.json
```

## Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create a `.env` file in the `backend` directory:
```bash
LEMLIST_API_KEY=your_api_key_here
```

6. Run the server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

## Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Adding shadcn/ui Components

To add shadcn/ui components, use the CLI:

```bash
cd frontend
npx shadcn-ui@latest add [component-name]
```

For example:
```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
```

## Dashboard

The dashboard displays running campaigns from lemlist with the following metrics:
- Campaign names
- Number of companies in campaign
- Number of people in campaign
- Number of people engaged
- Open rate (%)
- Reply rate (%)

Access the dashboard at `http://localhost:3000/dashboard`

## Technologies

- **Backend**: Python, FastAPI
- **Frontend**: React, Next.js 14, TypeScript, Tailwind CSS
- **UI Components**: shadcn/ui (configured, ready to use)
- **API Integration**: lemlist API

