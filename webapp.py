"""
Flask web server for the Task Manager demo app.
Demonstrates CRUD operations with the custom RDBMS.
"""

from flask import Flask, jsonify, request, send_from_directory
import os
import sys

# Add the RDBMS modules to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage import Database
from schema import TableSchema, Column
from datatypes import DataType
from exceptions import RDBMSError

app = Flask(__name__, static_folder='static')

# Initialize database and create tasks table
db = Database()

def init_database():
    """Initialize the database with the tasks table."""
    if not db.has_table('tasks'):
        schema = TableSchema(
            name='tasks',
            columns=[
                Column(name='id', data_type=DataType.INTEGER, primary_key=True),
                Column(name='title', data_type=DataType.TEXT, not_null=True),
                Column(name='description', data_type=DataType.TEXT),
                Column(name='priority', data_type=DataType.TEXT),
                Column(name='completed', data_type=DataType.BOOLEAN),
            ]
        )
        db.create_table(schema)

init_database()

# Track next ID for auto-increment
_next_id = 1

def get_next_id():
    global _next_id
    current = _next_id
    _next_id += 1
    return current


# ============================================================
# Static Files
# ============================================================

@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


# ============================================================
# REST API Endpoints
# ============================================================

@app.route('/api/tasks', methods=['GET'])
def list_tasks():
    """Get all tasks."""
    table = db.get_table('tasks')
    tasks = []
    for row in table.scan():
        tasks.append({
            'id': row['id'],
            'title': row['title'],
            'description': row['description'],
            'priority': row['priority'],
            'completed': row['completed']
        })
    return jsonify(tasks)


@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create a new task."""
    data = request.get_json()
    
    if not data or not data.get('title'):
        return jsonify({'error': 'Title is required'}), 400
    
    try:
        table = db.get_table('tasks')
        task_id = get_next_id()
        
        row = table.insert({
            'id': task_id,
            'title': data['title'],
            'description': data.get('description', ''),
            'priority': data.get('priority', 'medium'),
            'completed': False
        })
        
        return jsonify({
            'id': row['id'],
            'title': row['title'],
            'description': row['description'],
            'priority': row['priority'],
            'completed': row['completed']
        }), 201
    except RDBMSError as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Get a single task by ID."""
    table = db.get_table('tasks')
    rows = table.find_by_index('id', task_id)
    
    if not rows:
        return jsonify({'error': 'Task not found'}), 404
    
    row = rows[0]
    return jsonify({
        'id': row['id'],
        'title': row['title'],
        'description': row['description'],
        'priority': row['priority'],
        'completed': row['completed']
    })


@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update an existing task."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    table = db.get_table('tasks')
    rows = table.find_by_index('id', task_id)
    
    if not rows:
        return jsonify({'error': 'Task not found'}), 404
    
    row = rows[0]
    
    # Build update dict
    updates = {}
    if 'title' in data:
        updates['title'] = data['title']
    if 'description' in data:
        updates['description'] = data['description']
    if 'priority' in data:
        updates['priority'] = data['priority']
    if 'completed' in data:
        updates['completed'] = data['completed']
    
    try:
        updated_row = table.update(row.row_id, updates)
        return jsonify({
            'id': updated_row['id'],
            'title': updated_row['title'],
            'description': updated_row['description'],
            'priority': updated_row['priority'],
            'completed': updated_row['completed']
        })
    except RDBMSError as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task."""
    table = db.get_table('tasks')
    rows = table.find_by_index('id', task_id)
    
    if not rows:
        return jsonify({'error': 'Task not found'}), 404
    
    row = rows[0]
    table.delete(row.row_id)
    
    return jsonify({'message': 'Task deleted'}), 200


# ============================================================
# Main
# ============================================================

if __name__ == '__main__':
    print("🚀 Task Manager Demo")
    print("   Using custom RDBMS with B-tree indexing")
    print("   Open http://localhost:5050 in your browser")
    print("-" * 45)
    app.run(debug=True, port=5050)
