import json

def run_round_table(env, query_llm_fn):
    """
    Schema A: Structured Round Table
    A clean, sequential, turn-based rotation where peers take ordered turns 
    appending to a single shared room conversation log.
    """
    state = env.get_state()
    team_size = state.get("team_size", 3)
    agents = [f"Agent_{i+1}" for i in range(team_size)]
    
    for cycle in range(2):
        for agent in agents:
            current_state = env.get_state()
            prompt = f"You are {agent} in a structured turn-based round table of {team_size}. Add your input: {json.dumps(current_state)}"
            response = query_llm_fn(prompt)
            env.execute_action(agent, "speak", response)


def run_centralized(env, query_llm_fn):
    """
    Schema B: Centralized Hierarchy (Top-Down)
    Classic top-down control. A single Group Leader holds all administrative power, 
    routes tasks to subordinates, and owns exclusive write privileges to the final workspace.
    """
    state = env.get_state()
    team_size = state.get("team_size", 3)
    
    # 1. Central leader dictates structural allocation
    leader_prompt = f"You are the Group Leader. You hold sole authority. Assign parts for: {state['problem_statement']}"
    delegation_plan = query_llm_fn(leader_prompt)
    env.execute_action("Group_Leader", "speak", f"Master Plan: {delegation_plan}")
    
    # 2. Subordinate peers execute their specific slices in a silo
    peer_contributions = {}
    for i in range(1, team_size):
        peer_name = f"Agent_{i+1}"
        peer_prompt = f"You are subordinate {peer_name}. Return your work strictly to the leader: {delegation_plan}"
        peer_contributions[peer_name] = query_llm_fn(peer_prompt)
        
    # 3. Leader compiles the answers into the final block
    merge_prompt = f"You are the Group Leader. Compile these subordinate pieces: {json.dumps(peer_contributions)}"
    final_solution = query_llm_fn(merge_prompt)
    env.execute_action("Group_Leader", "write_scratchpad", final_solution)


def run_decentralized(env, query_llm_fn):
    """
    Schema C: True Decentralized Collaboration (Distributed Network)
    No central authority, no single point of control, and no rigid queues. 
    Autonomous peers interact dynamically and coordinate changes directly to 
    achieve a common goal via localized peer consensus.
    """
    state = env.get_state()
    team_size = state.get("team_size", 3)
    agents = [f"Agent_{i+1}" for i in range(team_size)]
    
    # Distributed iteration: Peers interact dynamically as equal nodes
    for event in range(3):
        for agent in agents:
            current_state = env.get_state()
            
            # Every agent acts as an independent node looking at the total network state
            decentralized_prompt = f"""
            You are {agent}, an autonomous participant in a decentralized, leaderless peer network.
            There is no top-down manager directing you. Coordinate directly with your peers.
            
            Current Distributed State Matrix:
            {json.dumps(current_state)}
            
            Based on current peer data, propose the next analytical patch, run an allowed tool, 
            or update the shared workspace directly to move the group toward completion.
            """
            response = query_llm_fn(decentralized_prompt)
            
            # Autonomous workspace commit routing
            if "ACTION:" in response and "|" in response:
                try:
                    parts = response.split("|")
                    tool = parts[0].replace("ACTION:", "").strip()
                    payload = parts[1].replace("PAYLOAD:", "").strip()
                    tool_output = env.execute_action(agent, tool, payload)
                    env.execute_action(agent, "speak", f"[Node Update] Executed {tool}: {tool_output}")
                except Exception:
                    env.execute_action(agent, "speak", response)
            else:
                env.execute_action(agent, "speak", response)