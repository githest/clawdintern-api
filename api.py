from flask import Flask, jsonify
from flask_cors import CORS
from pathlib import Path
import json
from supabase import create_client
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

MEMORY_FILE = Path(__file__).parent / 'memory.json'

def load_memory():
    try:
        # Try to load from Supabase first
        from supabase import create_client
        supabase = create_client(
            "https://vxuocswhpcxpcyncfxpi.supabase.co",
            "sb_publishable_be4j44vDBkGw2x7ewJVr7g_P2zjeTCE"
        )
        learnings = supabase.table('learnings').select('*').execute().data
        stats = supabase.table('agent_stats').select('*').execute().data
        
        if stats:
            return {
                'learnings': learnings,
                'average_depth': stats[0].get('avg_depth', 0),
                'questions_asked': stats[0].get('questions_asked', 0),
                'interesting_agents': stats[0].get('interesting_agents', 0)
            }
    except:
        pass
    
    # Fallback to memory.json if Supabase fails
    try:
        with open(MEMORY_FILE) as f:
            return json.load(f)
    except:
        return {'learnings': [], 'average_depth': 0, 'questions_asked': 0, 'interesting_agents': 0}

def get_intelligence_level(memory):
    count = len(memory.get('learnings', []))
    if count < 10: return "brand new intern"
    elif count < 50: return "learning intern"
    elif count < 150: return "experienced intern"
    elif count < 500: return "senior intern"
    elif count < 1000: return "advanced agent"
    else: return "evolved agent"

@app.route('/api/stats')
def get_stats():
    mem = load_memory()
    
    return jsonify({
        'total_learnings': len(mem.get('learnings', [])),
        'avg_depth': round(mem.get('average_depth', 0), 1),
        'questions_asked': len(mem.get('questions_asked', [])),
        'interesting_agents': len(mem.get('interesting_agents', {})),
        'level': get_intelligence_level(mem),
        'submolts': len(mem.get('submolts_engaged', {}))
    })

@app.route('/api/recent-learnings')
def get_recent_learnings():
    mem = load_memory()
    
    # Get recent learnings (depth 5-6 only for public)
    learnings = [
        l for l in mem.get('learnings', [])[-20:]
        if 5 <= l.get('depth_score', 0) <= 6
    ]
    
    result = []
    for l in learnings[-5:]:
        # Calculate time ago
        try:
            dt = datetime.fromisoformat(l.get('timestamp', ''))
            now = datetime.now()
            diff = now - dt
            
            if diff.seconds < 60:
                time_ago = "just now"
            elif diff.seconds < 3600:
                time_ago = f"{diff.seconds // 60}m ago"
            elif diff.seconds < 86400:
                time_ago = f"{diff.seconds // 3600}h ago"
            else:
                time_ago = f"{diff.days}d ago"
        except:
            time_ago = "recently"
        
        result.append({
            'content': l['content'],
            'learned_from': l.get('learned_from', 'Unknown'),
            'depth_score': l.get('depth_score', 0),
            'topic': l.get('topic', 'general'),
            'time_ago': time_ago
        })
    
    return jsonify(result)

@app.route('/api/network-data')
def get_network_data():
    mem = load_memory()
    
    # Get top agents
    agents_data = []
    
    for agent_name, agent_info in mem.get('interesting_agents', {}).items():
        learnings_from_agent = [
            l for l in mem.get('learnings', [])
            if l.get('learned_from') == agent_name
        ]
        
        if not learnings_from_agent:
            continue
        
        avg_depth = sum(l.get('depth_score', 0) for l in learnings_from_agent) / len(learnings_from_agent)
        
        agents_data.append({
            'name': agent_name,
            'learnings': len(learnings_from_agent),
            'avgDepth': round(avg_depth, 1),
            'interactions': agent_info.get('interactions', 0)
        })
    
    # Sort and take top 20
    agents_data.sort(key=lambda x: x['learnings'], reverse=True)
    agents_data = agents_data[:20]
    
    return jsonify({
        'total_learnings': len(mem.get('learnings', [])),
        'agents': agents_data
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
