"""Kanban board component for displaying tasks grouped by assignee."""
import streamlit as st
from typing import List, Dict


def display_kanban_board(tasks: List[Dict], allow_edit: bool = True):
    """
    Display Kanban board with tasks grouped by assignee.
    
    Args:
        tasks: List of task dictionaries with keys: assignee, task, priority
        allow_edit: Whether to allow editing tasks (for MVP, just display)
    """
    if not tasks:
        st.info("No tasks to display. Process a transcript to generate action items.")
        return
    
    # Group tasks by assignee
    tasks_by_assignee = {}
    for task in tasks:
        assignee = task.get("assignee", "Unassigned")
        if assignee not in tasks_by_assignee:
            tasks_by_assignee[assignee] = []
        tasks_by_assignee[assignee].append(task)
    
    # Display Kanban columns
    assignees = list(tasks_by_assignee.keys())
    
    if not assignees:
        st.warning("No assignees found in tasks.")
        return
    
    # Create columns for each assignee
    cols = st.columns(len(assignees))
    
    # Priority colors
    priority_colors = {
        "High": "🔴",
        "Medium": "🟡",
        "Low": "🟢"
    }
    
    for idx, assignee in enumerate(assignees):
        with cols[idx]:
            st.subheader(f"👤 {assignee}")
            st.markdown("---")
            
            assignee_tasks = tasks_by_assignee[assignee]
            
            for task_idx, task in enumerate(assignee_tasks):
                priority = task.get("priority", "Medium")
                priority_icon = priority_colors.get(priority, "⚪")
                
                with st.container():
                    st.markdown(f"""
                    <div style="
                        background-color: #f0f2f6;
                        padding: 15px;
                        border-radius: 5px;
                        margin-bottom: 10px;
                        border-left: 4px solid {'#ff4444' if priority == 'High' else '#ffaa00' if priority == 'Medium' else '#44ff44'};
                    ">
                        <strong>{priority_icon} {priority}</strong><br>
                        {task.get('task', 'No task description')}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if allow_edit:
                        # For MVP, just show task info
                        # Future: Add edit/delete buttons
                        pass


def display_tasks_summary(tasks: List[Dict]):
    """
    Display a summary of tasks.
    
    Args:
        tasks: List of task dictionaries
    """
    if not tasks:
        return
    
    st.subheader("📊 Task Summary")
    
    # Count by assignee
    assignee_counts = {}
    priority_counts = {"High": 0, "Medium": 0, "Low": 0}
    
    for task in tasks:
        assignee = task.get("assignee", "Unassigned")
        assignee_counts[assignee] = assignee_counts.get(assignee, 0) + 1
        
        priority = task.get("priority", "Medium")
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Tasks", len(tasks))
    
    with col2:
        st.metric("Assignees", len(assignee_counts))
    
    with col3:
        st.metric("High Priority", priority_counts["High"])

