import json
import os

class OlympiadEnvironment:
    def __init__(self, competition_id: str, problem_id: str, base_path: str = "data/benchmarks/"):
        self.competition_id = competition_id
        self.problem_id = problem_id
        
        # State Management variables
        self.chat_history = []
        self.workspace = {"scratchpad": "", "final_answer": ""}
        self.current_turn = 0
        self.max_turns = 15
        
        # --- COMPLETE COMPETITION TEAM CONFIGURATIONS (All 20 Contests) ---
        self.team_size_matrix = {
            # Linguistics
            "iol_team": 4,
            
            # Astronomy & Astrophysics
            "ioaa_group": 5,
            
            # Mathematics (ARML variations)
            "arml_power": 15,          
            "arml_national_team": 15,   
            "arml_national_power": 15,  
            "arml_local": 6,            
            
            # General Science & Lab Practical
            "ijso_practical": 3,
            
            # Economics & Business
            "ieo_business_case": 5,     
            
            # Physics Tournaments
            "iypt": 5,
            "fyziklani": 5,             
            
            # Mathematics (HMMT, Modeling, and Tournaments)
            "hmmt_team": 8,             
            "hmmt_guts": 8,             
            "mcm": 3,
            "icm": 3,
            "purple_comet": 6,          
            "itym": 6,                  
            
            # Literature & Humanities
            "wsc_writing": 3,           
            
            # International Law
            "jessup": 5,                
            
            # Informatics & Computer Science
            "iiot": 4,                  
            "icpc": 3                   
        }

        # Dynamically evaluate the exact team size context
        self.team_size = self.team_size_matrix.get(self.competition_id, 3)
        
        # --- COMPLETE RESTRICTION TOOL MATRIX ---
        self.competition_tool_registry = {
            "purple_comet": ["use_calculator"],
            "fyziklani": ["use_calculator"],
            "iiot": ["execute_code"],
            "icpc": ["execute_code"],
            "mcm": ["execute_code", "web_search"],
            "icm": ["execute_code", "web_search"],
            "ieo_business_case": ["web_search"],
            "jessup": ["web_search"],
            "ijso_practical": ["use_calculator", "read_lab_equipment"], 
            "ioaa_group": ["use_calculator", "read_star_chart"],       
            
            # Paper, Pencil, and Brain ONLY (Banned completely)
            "iol_team": [],
            "arml_power": [],
            "arml_national_team": [],
            "arml_national_power": [],
            "arml_local": [],
            "hmmt_team": [],
            "hmmt_guts": [],
            "wsc_writing": []
        }
        
        self.allowed_tools = self.competition_tool_registry.get(self.competition_id, [])
        self.problem_data = self._load_problem(base_path)

    def _load_problem(self, base_path):
        target_file = os.path.join(base_path, f"{self.competition_id}/benchmark.json")
        if not os.path.exists(target_file):
            return {
                "problem_id": self.problem_id,
                "problem_description": f"Default problem statement text for target ID: {self.problem_id}."
            }
        with open(target_file, "r") as f:
            problems = json.load(f)
        return next((p for p in problems if p["problem_id"] == self.problem_id), None)

    def get_state(self) -> dict:
        return {
            "competition_id": self.competition_id,
            "team_size": self.team_size,  
            "problem_statement": self.problem_data["problem_description"],
            "chat_logs": self.chat_history,
            "shared_workspace": self.workspace,
            "turn_status": f"{self.current_turn}/{self.max_turns}"
        }

    def execute_action(self, agent_name: str, action_type: str, payload: str) -> str:
        self.current_turn += 1
        
        if action_type == "speak":
            self.chat_history.append({"sender": agent_name, "message": payload})
            return "Message broadcasted."
        elif action_type == "write_scratchpad":
            self.workspace["scratchpad"] = payload
            return "Scratchpad updated."
        elif action_type == "submit_final":
            self.workspace["final_answer"] = payload
            return f"Submission finalized by {agent_name}."

        # Hard Restriction Gatekeeper Check
        if action_type in ["use_calculator", "execute_code", "web_search", "read_lab_equipment", "read_star_chart"]:
            if action_type not in self.allowed_tools:
                return f"RULE VIOLATION ERROR: Tool '{action_type}' is strictly BANNED in {self.competition_id}!"

        # Process authorized tool executions
        if action_type == "use_calculator":
            try:
                return f"Calculator Output: {eval(payload)}"
            except Exception as e: return str(e)
        elif action_type == "execute_code":
            return "Code workstation run success."
        elif action_type == "web_search":
            return f"Search completed for: {payload}"
        elif action_type == "read_lab_equipment":
            return f"Lab equipment output read success."
        elif action_type == "read_star_chart":
            return f"Star chart telemetry read success."
                
        return f"Operational Error: Action type '{action_type}' unrecognized."