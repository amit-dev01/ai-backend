from agents.tracking_agent import run as tracking_run
from agents.intelligence_agent import run as intelligence_run
from agents.strategy_agent import run as strategy_run
from agents.recommendation_agent import run as recommendation_run

# Replace with your real competitor ID
competitor_id = "04539402-dcf3-4599-b969-6c014a7e1720"

# Step 1: Tracking
tracking_data = tracking_run(competitor_id)

# Step 2: Intelligence
intelligence_data = intelligence_run(tracking_data)

# Step 3: Strategy
strategy_data = strategy_run(intelligence_data)

# Step 4: Recommendation
recommendation_data = recommendation_run(strategy_data)

print("\n=== RECOMMENDATION OUTPUT ===\n")
print(recommendation_data)