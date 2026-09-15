"""AWS Cost Explorer API endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import boto3
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/costs", tags=["costs"])

# Initialize Cost Explorer client
ce_client = boto3.client('ce', region_name='us-east-2')


class GetCostsRequest(BaseModel):
    """Request model for fetching costs."""
    account_ids: List[str]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    metric: str = "UnblendedCost"
    granularity: str = "DAILY"


class CostBreakdownRequest(BaseModel):
    """Request model for cost breakdown by service."""
    account_id: str
    days: int = 30
    metric: str = "UnblendedCost"


class GetCostsResponse(BaseModel):
    """Response model for costs."""
    costs_by_account: Dict
    total_costs: float
    projected_monthly: float
    period: Dict


@router.post("/get-costs")
async def get_costs(request: GetCostsRequest) -> GetCostsResponse:
    """
    Fetch actual AWS costs from Cost Explorer for multiple accounts.
    
    Args:
        account_ids: List of AWS account numbers (e.g., ["873363353263", "6574-7346-4918"])
        start_date: YYYY-MM-DD format (default: 30 days ago)
        end_date: YYYY-MM-DD format (default: today)
        metric: UnblendedCost, UsageQuantity, BlendedCost
        granularity: DAILY, MONTHLY
    
    Returns:
        Cost breakdown by account with totals and projections
    """
    try:
        if not request.end_date:
            request.end_date = datetime.utcnow().date().isoformat()
        if not request.start_date:
            request.start_date = (datetime.utcnow().date() - timedelta(days=30)).isoformat()
        
        logger.info(
            f"Fetching costs for {len(request.account_ids)} accounts "
            f"from {request.start_date} to {request.end_date}"
        )
        
        # Get cost and usage data
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': request.start_date,
                'End': request.end_date
            },
            Granularity=request.granularity,
            Metrics=[request.metric],
            Filter={
                'Dimensions': {
                    'Key': 'LINKED_ACCOUNT',
                    'Values': request.account_ids
                }
            },
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'LINKED_ACCOUNT'},
                {'Type': 'DIMENSION', 'Key': 'SERVICE'}
            ]
        )
        
        # Parse results by account
        costs_by_account = {}
        for result in response.get('ResultsByTime', []):
            for group in result.get('Groups', []):
                account_id = group['Keys'][0]
                service = group['Keys'][1]
                cost = float(group['Metrics'][request.metric]['Amount'])
                
                if account_id not in costs_by_account:
                    costs_by_account[account_id] = {
                        'total': 0,
                        'services': {}
                    }
                
                costs_by_account[account_id]['total'] += cost
                costs_by_account[account_id]['services'][service] = cost
        
        total_costs = sum(acc['total'] for acc in costs_by_account.values())
        
        # Get forecast for rest of month
        today = datetime.utcnow().date()
        month_start = today.replace(day=1)
        month_end = (today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        try:
            forecast_response = ce_client.get_cost_forecast(
                TimePeriod={
                    'Start': today.isoformat(),
                    'End': month_end.isoformat()
                },
                Metric=request.metric,
                Granularity='MONTHLY',
                Filter={
                    'Dimensions': {
                        'Key': 'LINKED_ACCOUNT',
                        'Values': request.account_ids
                    }
                }
            )
            
            projected_monthly = sum(
                float(item['MeanValue']) 
                for item in forecast_response.get('ForecastResultsByTime', [])
            )
        except Exception as forecast_error:
            logger.warning(f"Could not fetch forecast: {forecast_error}")
            # Estimate based on current month average
            days_elapsed = (today - month_start).days or 1
            projected_monthly = total_costs * (30 / days_elapsed)
        
        logger.info(f"Total costs: ${total_costs:.2f}, Projected monthly: ${projected_monthly:.2f}")
        
        return GetCostsResponse(
            costs_by_account=costs_by_account,
            total_costs=total_costs,
            projected_monthly=projected_monthly,
            period={'start': request.start_date, 'end': request.end_date}
        )
    
    except Exception as e:
        logger.error(f"Error fetching costs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch costs: {str(e)}")


@router.post("/get-cost-breakdown")
async def get_cost_breakdown(request: CostBreakdownRequest):
    """
    Get detailed cost breakdown by service for a single account.
    
    Args:
        account_id: AWS account ID
        days: Number of days to look back (default: 30)
        metric: UnblendedCost, UsageQuantity, BlendedCost
    
    Returns:
        Service-level cost breakdown
    """
    try:
        end_date = datetime.utcnow().date().isoformat()
        start_date = (datetime.utcnow().date() - timedelta(days=request.days)).isoformat()
        
        logger.info(
            f"Fetching cost breakdown for account {request.account_id} "
            f"from {start_date} to {end_date}"
        )
        
        response = ce_client.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='DAILY',
            Metrics=[request.metric],
            Filter={
                'Dimensions': {
                    'Key': 'LINKED_ACCOUNT',
                    'Values': [request.account_id]
                }
            },
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        service_costs = {}
        for result in response.get('ResultsByTime', []):
            for group in result.get('Groups', []):
                service = group['Keys'][0]
                cost = float(group['Metrics'][request.metric]['Amount'])
                service_costs[service] = service_costs.get(service, 0) + cost
        
        total = sum(service_costs.values())
        
        logger.info(f"Service breakdown for {request.account_id}: {len(service_costs)} services, ${total:.2f} total")
        
        return {
            'account_id': request.account_id,
            'services': service_costs,
            'total': total,
            'period': {'start': start_date, 'end': end_date}
        }
    
    except Exception as e:
        logger.error(f"Error fetching cost breakdown: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch cost breakdown: {str(e)}")


@router.get("/status")
async def cost_api_status():
    """Check if Cost Explorer API is accessible."""
    try:
        ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': datetime.utcnow().date().isoformat(),
                'End': datetime.utcnow().date().isoformat()
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
        return {'status': 'connected', 'service': 'AWS Cost Explorer'}
    except Exception as e:
        logger.error(f"Cost Explorer not accessible: {str(e)}")
        return {
            'status': 'error',
            'service': 'AWS Cost Explorer',
            'error': str(e)
        }
