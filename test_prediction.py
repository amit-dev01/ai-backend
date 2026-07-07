from agents.tracking_agent import run as tracking_run
from agents.intelligence_agent import run as intelligence_run
from agents.strategy_agent import run as strategy_run
from agents.recommendation_agent import run as recommendation_run
from agents.prediction_agent import run as prediction_run

competitor_id = "04539402-dcf3-4599-b969-6c014a7e1720"

tracking_data = tracking_run(competitor_id)
intelligence_data = intelligence_run(tracking_data)
strategy_data = strategy_run(intelligence_data)
recommendation_data = recommendation_run(strategy_data)
prediction_data = prediction_run(intelligence_data)

print("\n=== PREDICTION OUTPUT ===\n")
print(prediction_data)