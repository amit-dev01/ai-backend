from agents.tracking_agent import run as tracking_run
from agents.intelligence_agent import run as intelligence_run

competitor_id = "04539402-dcf3-4599-b969-6c014a7e1720"

tracking_data = tracking_run(competitor_id)

intelligence_data = intelligence_run(tracking_data)

print("\n=== AI INTELLIGENCE OUTPUT ===\n")
print(intelligence_data)