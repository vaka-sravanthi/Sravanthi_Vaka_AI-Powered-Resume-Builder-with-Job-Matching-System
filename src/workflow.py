from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional, Union
import math

import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from .agents import AgentResult


@dataclass
class WorkflowTrace:
    steps: List[AgentResult]
    edges: List[Tuple[str, str]]
    metadata: Optional[Dict[str, Any]] = None


def build_workflow_trace(steps: List[AgentResult]) -> WorkflowTrace:
    names = [s.name for s in steps]
    edges: List[Tuple[str, str]] = [(names[i], names[i + 1]) for i in range(len(names) - 1)]
    
    metadata = {
        'total_steps': len(steps),
        'execution_order': names,
        'step_types': [classify_agent_type(s.name) for s in steps],
        'processing_times': [estimate_processing_time(s) for s in steps]
    }
    
    return WorkflowTrace(steps=steps, edges=edges, metadata=metadata)


def classify_agent_type(name: str) -> str:
    name_lower = name.lower()
    
    if any(word in name_lower for word in ['skills', 'skill']):
        if 'extract' in name_lower or 'parse' in name_lower:
            return 'skills_extractor'
        elif 'match' in name_lower or 'score' in name_lower:
            return 'skills_matcher'
        elif 'enhance' in name_lower or 'suggest' in name_lower:
            return 'skills_enhancer'
        else:
            return 'skills_processor'
    
    elif 'resume' in name_lower or 'cv' in name_lower:
        if 'parse' in name_lower or 'extract' in name_lower:
            return 'resume_parser'
        elif 'enhance' in name_lower or 'improve' in name_lower:
            return 'resume_enhancer'
        else:
            return 'resume_processor'
    
    elif 'job' in name_lower:
        if 'parse' in name_lower or 'extract' in name_lower:
            return 'job_parser'
        elif 'match' in name_lower or 'recommend' in name_lower:
            return 'job_matcher'
        else:
            return 'job_processor'
    
    elif 'content' in name_lower or 'generate' in name_lower:
        return 'content_generator'
    elif 'embedding' in name_lower or 'vector' in name_lower:
        return 'embedding_processor'
    elif 'report' in name_lower:
        return 'report_generator'
    
    elif 'parser' in name_lower or 'extract' in name_lower:
        return 'parser'
    elif 'enhance' in name_lower:
        return 'enhancer'
    elif 'match' in name_lower or 'score' in name_lower:
        return 'analyzer'
    else:
        return 'generic'


def estimate_processing_time(step: AgentResult) -> float:
    if not step.outputs:
        return 1.0
    
    complexity = 0
    for key, value in step.outputs.items():
        if isinstance(value, (list, tuple)):
            complexity += len(value) * 0.1
        elif isinstance(value, str):
            complexity += len(value) * 0.001
        elif isinstance(value, dict):
            complexity += len(value) * 0.2
        else:
            complexity += 0.5
    
    return max(0.5, min(complexity, 10.0))


def get_agent_color_scheme() -> Dict[str, Dict[str, str]]:
    return {
        'skills_extractor': {
            'primary': '#FF6B6B',
            'secondary': '#FF8E8E', 
            'text': '#FFFFFF',
            'border': '#FF4757'
        },
        'skills_matcher': {
            'primary': '#4ECDC4',
            'secondary': '#6BCCC4',
            'text': '#FFFFFF',
            'border': '#26A69A'
        },
        'skills_enhancer': {
            'primary': '#A8E6CF',
            'secondary': '#B8E6D2',
            'text': '#2C3E50',
            'border': '#2ECC71'
        },
        'skills_processor': {
            'primary': '#FFB347',
            'secondary': '#FFC266',
            'text': '#2C3E50', 
            'border': '#FF8C00'
        },
        
        'resume_parser': {
            'primary': '#9B59B6',
            'secondary': '#B370CF',
            'text': '#FFFFFF',
            'border': '#8E44AD'
        },
        'resume_enhancer': {
            'primary': '#3498DB',
            'secondary': '#5DADE2',
            'text': '#FFFFFF',
            'border': '#2980B9'
        },
        'resume_processor': {
            'primary': '#E67E22',
            'secondary': '#F39C12',
            'text': '#FFFFFF',
            'border': '#D68910'
        },
        
        'job_parser': {
            'primary': '#2ECC71',
            'secondary': '#58D68D',
            'text': '#FFFFFF',
            'border': '#27AE60'
        },
        'job_matcher': {
            'primary': '#E74C3C',
            'secondary': '#EC7063',
            'text': '#FFFFFF',
            'border': '#C0392B'
        },
        'job_processor': {
            'primary': '#F39C12',
            'secondary': '#F8C471',
            'text': '#2C3E50',
            'border': '#E67E22'
        },
        
        'content_generator': {
            'primary': '#FF7675',
            'secondary': '#FD79A8',
            'text': '#FFFFFF',
            'border': '#E84393'
        },
        'embedding_processor': {
            'primary': '#6C5CE7',
            'secondary': '#A29BFE',
            'text': '#FFFFFF',
            'border': '#5F3DC4'
        },
        'report_generator': {
            'primary': '#00B894',
            'secondary': '#00CEC9',
            'text': '#FFFFFF',
            'border': '#00A085'
        },
        
        'parser': {
            'primary': '#FF6B6B',
            'secondary': '#FF8E8E',
            'text': '#FFFFFF',
            'border': '#FF4757'
        },
        'enhancer': {
            'primary': '#4ECDC4',
            'secondary': '#6BCCC4',
            'text': '#FFFFFF', 
            'border': '#26A69A'
        },
        'analyzer': {
            'primary': '#45B7D1',
            'secondary': '#6BC5D9',
            'text': '#FFFFFF',
            'border': '#3498DB'
        },
        'generic': {
            'primary': '#FFEAA7',
            'secondary': '#FDCB6E',
            'text': '#2C3E50',
            'border': '#F39C12'
        },
        'error': {
            'primary': '#E74C3C',
            'secondary': '#EC7063',
            'text': '#FFFFFF',
            'border': '#C0392B'
        }
    }


def get_skills_icon(agent_type: str) -> str:
    icons = {
        'skills_extractor': '🔍',
        'skills_matcher': '🎯',
        'skills_enhancer': '✨',
        'skills_processor': '⚙️',
        'resume_parser': '📄',
        'resume_enhancer': '📝',
        'resume_processor': '📋',
        'job_parser': '💼',
        'job_matcher': '🤝',
        'job_processor': '🏢',
        'content_generator': '🤖',
        'embedding_processor': '🧠',
        'report_generator': '📊',
        'parser': '🔍',
        'enhancer': '✨',
        'analyzer': '📈',
        'generic': '⚡',
        'error': '❌'
    }
    return icons.get(agent_type, '⚙️')


def workflow_figure(trace: WorkflowTrace, style: str = "skills_focused") -> go.Figure:
    if style == "skills_focused":
        return create_skills_matching_workflow(trace)
    elif style == "modern":
        return create_modern_workflow(trace)
    elif style == "timeline":
        return create_timeline_workflow(trace)
    elif style == "circular":
        return create_circular_workflow(trace)
    elif style == "hierarchical":
        return create_hierarchical_workflow(trace)
    elif style == "sankey":
        return create_sankey_workflow(trace)
    else:
        return create_enhanced_default_workflow(trace)


def create_skills_matching_workflow(trace: WorkflowTrace) -> go.Figure:
    steps = trace.steps
    color_scheme = get_agent_color_scheme()
    
    fig = go.Figure()
    
    positions = {}
    n_steps = len(steps)
    
    for i, step in enumerate(steps):
        agent_type = classify_agent_type(step.name)
        
        if agent_type in ['resume_parser', 'skills_extractor']:
            positions[step.name] = (0, 1)
        elif agent_type in ['job_parser', 'job_processor']:
            positions[step.name] = (0, -1)
        elif agent_type in ['skills_matcher', 'analyzer']:
            positions[step.name] = (2, 0)
        elif agent_type in ['skills_enhancer', 'resume_enhancer', 'content_generator']:
            positions[step.name] = (4, 0)
        elif agent_type in ['report_generator']:
            positions[step.name] = (5, 0)
        else:
            positions[step.name] = (i * 1.5, 0)
    
    for i in range(len(steps) - 1):
        current_step = steps[i]
        next_step = steps[i + 1]
        
        x0, y0 = positions[current_step.name]
        x1, y1 = positions[next_step.name]
        
        fig.add_trace(go.Scatter(
            x=[x0, (x0 + x1) / 2, x1],
            y=[y0, (y0 + y1) / 2 + 0.2, y1],
            mode='lines',
            line=dict(
                color='rgba(52, 152, 219, 0.6)',
                width=3,
                shape='spline'
            ),
            showlegend=False,
            hoverinfo='none'
        ))
        
        fig.add_trace(go.Scatter(
            x=[x1],
            y=[y1],
            mode='markers',
            marker=dict(
                symbol='triangle-right',
                size=12,
                color='rgba(52, 152, 219, 0.8)',
                angle=math.degrees(math.atan2(y1 - y0, x1 - x0)) if x1 != x0 else 0
            ),
            showlegend=False,
            hoverinfo='none'
        ))
    
    for step in steps:
        x, y = positions[step.name]
        agent_type = classify_agent_type(step.name)
        colors = color_scheme.get(agent_type, color_scheme['generic'])
        
        icon = get_skills_icon(agent_type)
        
        fig.add_trace(go.Scatter(
            x=[x],
            y=[y],
            mode='markers+text',
            text=[f"{icon}<br>{step.name.replace(' ', '<br>')}"],
            textposition='middle center',
            textfont=dict(
                size=11,
                color=colors['text'],
                family="Arial Black"
            ),
            marker=dict(
                size=100,
                color=colors['primary'],
                line=dict(width=4, color=colors['border']),
                opacity=0.9,
                symbol='circle'
            ),
            hovertext=[create_skills_hover_text(step)],
            hovertemplate='%{hovertext}<extra></extra>',
            showlegend=False
        ))
    
    fig.update_layout(
        title={
            'text': "🎯 Skills Matching AI Workflow",
            'x': 0.5,
            'font': {'size': 24, 'family': 'Arial Black', 'color': '#2C3E50'}
        },
        showlegend=False,
        hovermode='closest',
        xaxis=dict(
            range=[-1, 6],
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        yaxis=dict(
            range=[-2, 2],
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        plot_bgcolor='rgba(248, 249, 250, 0.95)',
        paper_bgcolor='white',
        height=500,
        margin=dict(l=40, r=40, t=80, b=40)
    )
    
    return fig


def create_sankey_workflow(trace: WorkflowTrace) -> go.Figure:
    steps = trace.steps
    
    nodes = [step.name for step in steps]
    node_indices = {name: i for i, name in enumerate(nodes)}
    
    sources = []
    targets = []
    values = []
    
    for i in range(len(steps) - 1):
        sources.append(i)
        targets.append(i + 1)
        values.append(1)
    
    color_scheme = get_agent_color_scheme()
    node_colors = []
    for step in steps:
        agent_type = classify_agent_type(step.name)
        colors = color_scheme[agent_type]
        node_colors.append(colors['primary'])
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=nodes,
            color=node_colors
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color='rgba(52, 152, 219, 0.4)'
        )
    )])
    
    fig.update_layout(
        title={
            'text': "🌊 Skills Matching Flow",
            'x': 0.5,
            'font': {'size': 20, 'family': 'Arial Black', 'color': '#2C3E50'}
        },
        font_size=12,
        height=400,
        margin=dict(l=40, r=40, t=80, b=40)
    )
    
    return fig


def create_enhanced_default_workflow(trace: WorkflowTrace) -> go.Figure:
    g = nx.DiGraph()
    color_scheme = get_agent_color_scheme()
    
    for s in trace.steps:
        g.add_node(s.name)
    for u, v in trace.edges:
        g.add_edge(u, v)

    pos = nx.spring_layout(g, seed=42, k=2, iterations=50)

    edge_x, edge_y = [], []
    for u, v in g.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    node_x, node_y, text, hover_texts, colors = [], [], [], [], []
    name_to_step = {s.name: s for s in trace.steps}
    
    for n in g.nodes():
        x, y = pos[n]
        node_x.append(x)
        node_y.append(y)
        text.append(n)
        
        step = name_to_step.get(n)
        agent_type = classify_agent_type(n)
        color_info = color_scheme[agent_type]
        
        hover_text = create_skills_hover_text(step)
        hover_texts.append(hover_text)
        
        reasoning = step.reasoning if step else ""
        if reasoning and "fallback" in reasoning.lower():
            colors.append(color_scheme['error']['primary'])
        else:
            colors.append(color_info['primary'])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=3, color="rgba(128, 128, 128, 0.6)"),
        hoverinfo="none",
        mode="lines",
        showlegend=False
    )
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=text,
        textposition="bottom center",
        textfont=dict(size=12, family="Arial Black"),
        hoverinfo="text",
        hovertext=hover_texts,
        hovertemplate="%{hovertext}<extra></extra>",
        marker=dict(
            showscale=False,
            color=colors,
            size=60,
            line=dict(width=3, color="#fff"),
            opacity=0.9
        ),
        showlegend=False
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    
    fig.update_layout(
        title={
            'text': "🚀 Enhanced Skills Workflow",
            'x': 0.5,
            'font': {'size': 20, 'family': 'Arial Black', 'color': '#2C3E50'}
        },
        showlegend=False,
        hovermode="closest",
        margin=dict(l=40, r=40, t=80, b=40),
        plot_bgcolor='rgba(248, 249, 250, 0.95)',
        paper_bgcolor='white',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=500
    )
    
    return fig


def create_skills_hover_text(step: AgentResult) -> str:
    if not step:
        return "No step information available"
    
    inputs = step.inputs if step else {}
    outputs = step.outputs if step else {}
    reasoning = step.reasoning if step else ""
    
    skills_info = ""
    if 'skills' in str(outputs).lower() or 'matched' in str(outputs).lower():
        if isinstance(outputs, dict):
            for key, value in outputs.items():
                if 'skill' in key.lower():
                    if isinstance(value, list):
                        skills_info += f"<br>🎯 {key}: {len(value)} items"
                    elif isinstance(value, (int, float)):
                        skills_info += f"<br>📊 {key}: {value}"
                elif 'match' in key.lower() or 'score' in key.lower():
                    skills_info += f"<br>📈 {key}: {value}"
    
    def _summarize(d: Dict[str, Any], max_items: int = 3) -> str:
        if not d:
            return "None"
        
        items = []
        for k, v in list(d.items())[:max_items]:
            if isinstance(v, (list, tuple)):
                items.append(f"📝 {k}: [{len(v)} items]")
            elif isinstance(v, (int, float)):
                items.append(f"🔢 {k}: {v}")
            elif isinstance(v, str):
                preview = v.replace("\n", " ")[:40]
                items.append(f"📄 {k}: {preview}{'...' if len(v) > 40 else ''}")
            elif isinstance(v, dict):
                items.append(f"📂 {k}: {{{len(v)} keys}}")
            else:
                items.append(f"🔹 {k}: {str(v)[:25]}{'...' if len(str(v)) > 25 else ''}")
        
        if len(d) > max_items:
            items.append(f"... and {len(d) - max_items} more")
        
        return "<br>".join(items)
    
    agent_type = classify_agent_type(step.name)
    icon = get_skills_icon(agent_type)
    
    hover_text = f"""
    <b>{icon} {step.name}</b><br>
    <b>Type:</b> {agent_type.replace('_', ' ').title()}<br>
    {skills_info}<br>
    <b>📥 Inputs:</b><br>
    {_summarize(inputs)}<br>
    <br>
    <b>📤 Outputs:</b><br>
    {_summarize(outputs)}<br>
    <br>
    <b>🧠 Process:</b><br>
    {reasoning[:120]+'...' if len(reasoning) > 120 else reasoning}
    """
    
    return hover_text.strip()


def create_manual_hierarchical_layout(steps: List[AgentResult]) -> Dict[str, Tuple[float, float]]:
    pos = {}
    n_steps = len(steps)
    
    for i, step in enumerate(steps):
        pos[step.name] = (0, n_steps - i - 1)
    
    return pos


def create_modern_workflow(trace: WorkflowTrace) -> go.Figure:
    g = nx.DiGraph()
    color_scheme = get_agent_color_scheme()
    
    for s in trace.steps:
        g.add_node(s.name, agent_type=classify_agent_type(s.name))
    for u, v in trace.edges:
        g.add_edge(u, v)

    pos = nx.spring_layout(g, seed=42, k=3, iterations=50)
    
    edge_traces = []
    for i, (u, v) in enumerate(g.edges()):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        
        mid_x = (x0 + x1) / 2 + 0.1 * math.sin(i)
        mid_y = (y0 + y1) / 2 + 0.1 * math.cos(i)
        
        edge_trace = go.Scatter(
            x=[x0, mid_x, x1],
            y=[y0, mid_y, y1],
            mode='lines',
            line=dict(
                width=3,
                color='rgba(128, 128, 128, 0.6)',
                shape='spline'
            ),
            hoverinfo='none',
            showlegend=False
        )
        edge_traces.append(edge_trace)
        
        arrow_trace = go.Scatter(
            x=[x1],
            y=[y1],
            mode='markers',
            marker=dict(
                symbol='triangle-right',
                size=12,
                color='rgba(128, 128, 128, 0.8)'
            ),
            hoverinfo='none',
            showlegend=False
        )
        edge_traces.append(arrow_trace)

    node_traces = []
    name_to_step = {s.name: s for s in trace.steps}
    
    for node_name in g.nodes():
        x, y = pos[node_name]
        step = name_to_step.get(node_name)
        agent_type = classify_agent_type(node_name)
        colors = color_scheme[agent_type]
        
        hover_text = create_skills_hover_text(step)
        
        node_trace = go.Scatter(
            x=[x],
            y=[y],
            mode='markers+text',
            text=[node_name.replace(' ', '<br>')],
            textposition='middle center',
            textfont=dict(
                size=12,
                color=colors['text'],
                family="Arial Black"
            ),
            hovertext=[hover_text],
            hovertemplate='%{hovertext}<extra></extra>',
            marker=dict(
                size=80,
                color=colors['primary'],
                line=dict(width=4, color=colors['border']),
                opacity=0.9
            ),
            showlegend=False
        )
        node_traces.append(node_trace)
        
        glow_trace = go.Scatter(
            x=[x],
            y=[y],
            mode='markers',
            marker=dict(
                size=100,
                color=colors['secondary'],
                opacity=0.3,
                line=dict(width=0)
            ),
            hoverinfo='none',
            showlegend=False
        )
        node_traces.append(glow_trace)

    fig = go.Figure(data=edge_traces + node_traces)
    
    fig.update_layout(
        title={
            'text': "🤖 AI Workflow Execution Pipeline",
            'x': 0.5,
            'font': {'size': 24, 'family': 'Arial Black', 'color': '#2C3E50'}
        },
        showlegend=False,
        hovermode='closest',
        margin=dict(l=40, r=40, t=80, b=40),
        plot_bgcolor='rgba(248, 249, 250, 0.95)',
        paper_bgcolor='white',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=600
    )
    
    return fig


def create_timeline_workflow(trace: WorkflowTrace) -> go.Figure:
    fig = go.Figure()
    
    color_scheme = get_agent_color_scheme()
    steps = trace.steps
    n_steps = len(steps)
    
    x_positions = list(range(n_steps))
    y_position = 0
    
    fig.add_trace(go.Scatter(
        x=[-0.5, n_steps - 0.5],
        y=[y_position, y_position],
        mode='lines',
        line=dict(color='#BDC3C7', width=4),
        showlegend=False,
        hoverinfo='none'
    ))
    
    for i, step in enumerate(steps):
        agent_type = classify_agent_type(step.name)
        colors = color_scheme[agent_type]
        icon = get_skills_icon(agent_type)
        
        fig.add_trace(go.Scatter(
            x=[i],
            y=[y_position],
            mode='markers+text',
            text=[f"{icon}<br>Step {i+1}"],
            textposition='top center',
            textfont=dict(size=12, color=colors['primary'], family="Arial Black"),
            marker=dict(
                size=60,
                color=colors['primary'],
                line=dict(width=3, color='white'),
                symbol='circle'
            ),
            hovertext=[create_skills_hover_text(step)],
            hovertemplate='%{hovertext}<extra></extra>',
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=[i],
            y=[y_position - 0.3],
            mode='text',
            text=[step.name.replace(' ', '<br>')],
            textfont=dict(size=10, color='#2C3E50'),
            showlegend=False,
            hoverinfo='none'
        ))
        
        if trace.metadata and 'processing_times' in trace.metadata:
            processing_time = trace.metadata['processing_times'][i]
            fig.add_trace(go.Scatter(
                x=[i],
                y=[y_position + 0.3],
                mode='text',
                text=[f"⏱️ {processing_time:.1f}s"],
                textfont=dict(size=9, color='#7F8C8D'),
                showlegend=False,
                hoverinfo='none'
            ))

    fig.update_layout(
        title={
            'text': "📊 Skills Matching Timeline",
            'x': 0.5,
            'font': {'size': 20, 'family': 'Arial Black', 'color': '#2C3E50'}
        },
        xaxis=dict(
            range=[-0.8, n_steps - 0.2],
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        yaxis=dict(
            range=[-0.8, 0.8],
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        plot_bgcolor='rgba(248, 249, 250, 0.95)',
        paper_bgcolor='white',
        height=400,
        margin=dict(l=40, r=40, t=80, b=40)
    )
    
    return fig


def create_circular_workflow(trace: WorkflowTrace) -> go.Figure:
    steps = trace.steps
    n_steps = len(steps)
    color_scheme = get_agent_color_scheme()
    
    angles = [2 * math.pi * i / n_steps for i in range(n_steps)]
    radius = 2
    x_positions = [radius * math.cos(angle) for angle in angles]
    y_positions = [radius * math.sin(angle) for angle in angles]
    
    fig = go.Figure()
    
    for i in range(n_steps):
        start_idx = i
        end_idx = (i + 1) % n_steps
        
        fig.add_trace(go.Scatter(
            x=[x_positions[start_idx], x_positions[end_idx]],
            y=[y_positions[start_idx], y_positions[end_idx]],
            mode='lines',
            line=dict(
                color='rgba(52, 152, 219, 0.6)',
                width=3,
                shape='spline'
            ),
            showlegend=False,
            hoverinfo='none'
        ))
        
        mid_x = (x_positions[start_idx] + x_positions[end_idx]) / 2
        mid_y = (y_positions[start_idx] + y_positions[end_idx]) / 2
        
        fig.add_trace(go.Scatter(
            x=[mid_x],
            y=[mid_y],
            mode='markers',
            marker=dict(
                symbol='triangle-right',
                size=10,
                color='#3498DB',
                angle=math.degrees(angles[end_idx])
            ),
            showlegend=False,
            hoverinfo='none'
        ))
    
    for i, step in enumerate(steps):
        agent_type = classify_agent_type(step.name)
        colors = color_scheme[agent_type]
        icon = get_skills_icon(agent_type)
        
        fig.add_trace(go.Scatter(
            x=[x_positions[i]],
            y=[y_positions[i]],
            mode='markers+text',
            text=[f"{icon}<br>{i+1}"],
            textfont=dict(size=14, color=colors['text'], family="Arial Black"),
            marker=dict(
                size=70,
                color=colors['primary'],
                line=dict(width=3, color='white')
            ),
            hovertext=[create_skills_hover_text(step)],
            hovertemplate='%{hovertext}<extra></extra>',
            showlegend=False
        ))
        
        text_radius = radius + 0.5
        text_x = text_radius * math.cos(angles[i])
        text_y = text_radius * math.sin(angles[i])
        
        fig.add_trace(go.Scatter(
            x=[text_x],
            y=[text_y],
            mode='text',
            text=[step.name],
            textfont=dict(size=10, color='#2C3E50'),
            showlegend=False,
            hoverinfo='none'
        ))
    
    fig.update_layout(
        title={
            'text': "🔄 Circular Skills Workflow",
            'x': 0.5,
            'font': {'size': 20, 'family': 'Arial Black', 'color': '#2C3E50'}
        },
        xaxis=dict(
            range=[-3.5, 3.5],
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            scaleanchor="y",
            scaleratio=1
        ),
        yaxis=dict(
            range=[-3.5, 3.5],
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        plot_bgcolor='rgba(248, 249, 250, 0.95)',
        paper_bgcolor='white',
        height=600,
        width=600,
        margin=dict(l=40, r=40, t=80, b=40)
    )
    
    return fig


def create_hierarchical_workflow(trace: WorkflowTrace) -> go.Figure:
    g = nx.DiGraph()
    for s in trace.steps:
        g.add_node(s.name)
    for u, v in trace.edges:
        g.add_edge(u, v)
    
    try:
        pos = nx.nx_agraph.graphviz_layout(g, prog='dot')
    except:
        pos = create_manual_hierarchical_layout(trace.steps)
    
    color_scheme = get_agent_color_scheme()
    name_to_step = {s.name: s for s in trace.steps}
    
    fig = go.Figure()
    
    for u, v in g.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        
        fig.add_trace(go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode='lines',
            line=dict(
                width=3,
                color='rgba(149, 165, 166, 0.8)'
            ),
            showlegend=False,
            hoverinfo='none'
        ))
        
        fig.add_trace(go.Scatter(
            x=[x1],
            y=[y1],
            mode='markers',
            marker=dict(
                symbol='triangle-up',
                size=12,
                color='rgba(149, 165, 166, 0.8)'
            ),
            showlegend=False,
            hoverinfo='none'
        ))
    
    for node_name in g.nodes():
        x, y = pos[node_name]
        step = name_to_step.get(node_name)
        agent_type = classify_agent_type(node_name)
        colors = color_scheme[agent_type]
        icon = get_skills_icon(agent_type)
        
        fig.add_trace(go.Scatter(
            x=[x],
            y=[y],
            mode='markers+text',
            text=[f"{icon}<br>{node_name.replace(' ', '<br>')}"],
            textposition='middle center',
            textfont=dict(size=10, color=colors['text'], family="Arial"),
            marker=dict(
                size=100,
                color=colors['primary'],
                line=dict(width=2, color='white'),
                symbol='square'
            ),
            hovertext=[create_skills_hover_text(step)],
            hovertemplate='%{hovertext}<extra></extra>',
            showlegend=False
        ))
    
    fig.update_layout(
        title={
            'text': "🏗️ Hierarchical Skills Workflow",
            'x': 0.5,
            'font': {'size': 20, 'family': 'Arial Black', 'color': '#2C3E50'}
        },
        showlegend=False,
        hovermode='closest',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='rgba(248, 249, 250, 0.95)',
        paper_bgcolor='white',
        height=600,
        margin=dict(l=40, r=40, t=80, b=40)
    )
    
    return fig


def create_workflow_metrics_dashboard(trace: WorkflowTrace) -> go.Figure:
    if not trace.metadata:
        return go.Figure()
    
    steps = trace.steps
    processing_times = trace.metadata.get('processing_times', [1.0] * len(steps))
    step_types = trace.metadata.get('step_types', ['generic'] * len(steps))
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Processing Time by Step",
            "Agent Type Distribution", 
            "Output Complexity",
            "Skills Matching Progress"
        ),
        specs=[[{"type": "bar"}, {"type": "pie"}],
               [{"type": "scatter"}, {"type": "scatter"}]]
    )
    
    colors = []
    for step in steps:
        agent_type = classify_agent_type(step.name)
        color_scheme = get_agent_color_scheme()
        colors.append(color_scheme[agent_type]['primary'])
    
    fig.add_trace(
        go.Bar(
            x=[s.name for s in steps],
            y=processing_times,
            marker_color=colors,
            name="Processing Time"
        ),
        row=1, col=1
    )
    
    type_counts = {}
    for agent_type in step_types:
        type_counts[agent_type] = type_counts.get(agent_type, 0) + 1
    
    fig.add_trace(
        go.Pie(
            labels=[t.replace('_', ' ').title() for t in type_counts.keys()],
            values=list(type_counts.values()),
            name="Agent Types"
        ),
        row=1, col=2
    )
    
    complexities = [len(str(s.outputs)) for s in steps]
    fig.add_trace(
        go.Scatter(
            x=list(range(len(steps))),
            y=complexities,
            mode='lines+markers',
            marker_color='#E74C3C',
            name="Output Size"
        ),
        row=2, col=1
    )
    
    skills_progress = []
    total_skills = 0
    for step in steps:
        if step.outputs and isinstance(step.outputs, dict):
            for key, value in step.outputs.items():
                if 'skill' in key.lower() and isinstance(value, (list, tuple)):
                    total_skills += len(value)
        skills_progress.append(total_skills)
    
    fig.add_trace(
        go.Scatter(
            x=list(range(len(steps))),
            y=skills_progress,
            mode='lines+markers',
            fill='tonexty',
            marker_color='#2ECC71',
            name="Skills Found"
        ),
        row=2, col=2
    )
    
    fig.update_layout(
        title="📊 Skills Matching Analytics Dashboard",
        height=700,
        showlegend=False
    )
    
    return fig


def get_available_workflow_styles() -> List[Dict[str, str]]:
    return [
        {"name": "Skills Focused", "value": "skills_focused", "description": "Optimized for skills matching workflow"},
        {"name": "Modern", "value": "modern", "description": "Sleek modern design with glow effects"},
        {"name": "Timeline", "value": "timeline", "description": "Linear timeline showing execution order"},
        {"name": "Circular", "value": "circular", "description": "Circular flow diagram"},
        {"name": "Hierarchical", "value": "hierarchical", "description": "Top-down hierarchical layout"},
        {"name": "Sankey", "value": "sankey", "description": "Flow-based Sankey diagram"},
        {"name": "Enhanced Default", "value": "enhanced", "description": "Enhanced version of original design"}
    ]


def create_workflow_comparison_view(traces: List[WorkflowTrace]) -> go.Figure:
    if not traces:
        return go.Figure()
    
    fig = make_subplots(
        rows=len(traces), cols=1,
        subplot_titles=[f"Workflow {i+1}: {len(trace.steps)} steps" for i, trace in enumerate(traces)],
        vertical_spacing=0.1
    )
    
    color_scheme = get_agent_color_scheme()
    
    for row, trace in enumerate(traces, 1):
        steps = trace.steps
        processing_times = trace.metadata.get('processing_times', [1.0] * len(steps)) if trace.metadata else [1.0] * len(steps)
        
        colors = []
        for step in steps:
            agent_type = classify_agent_type(step.name)
            colors.append(color_scheme[agent_type]['primary'])
        
        fig.add_trace(
            go.Bar(
                x=[s.name for s in steps],
                y=processing_times,
                marker_color=colors,
                name=f"Workflow {row}",
                showlegend=False
            ),
            row=row, col=1
        )
    
    fig.update_layout(
        title="🔀 Skills Workflow Comparison",
        height=300 * len(traces),
        showlegend=False
    )
    
    return fig


def create_skills_performance_summary(trace: WorkflowTrace) -> Dict[str, Any]:
    if not trace.steps:
        return {}
    
    summary = {
        'total_steps': len(trace.steps),
        'skills_extracted': 0,
        'skills_matched': 0,
        'match_percentage': 0.0,
        'processing_efficiency': calculate_workflow_efficiency(trace),
        'step_breakdown': {}
    }
    
    for step in trace.steps:
        agent_type = classify_agent_type(step.name)
        step_info = {
            'type': agent_type,
            'icon': get_skills_icon(agent_type)
        }
        
        if step.outputs and isinstance(step.outputs, dict):
            for key, value in step.outputs.items():
                if 'skill' in key.lower():
                    if isinstance(value, (list, tuple)):
                        if 'extract' in key.lower():
                            summary['skills_extracted'] = len(value)
                        elif 'match' in key.lower():
                            summary['skills_matched'] = len(value)
                        step_info[key] = len(value)
                    elif isinstance(value, (int, float)):
                        step_info[key] = value
                elif 'match' in key.lower() or 'score' in key.lower():
                    if isinstance(value, (int, float)):
                        summary['match_percentage'] = value
                        step_info[key] = value
        
        summary['step_breakdown'][step.name] = step_info
    
    return summary


def create_animated_skills_workflow(trace: WorkflowTrace) -> go.Figure:
    steps = trace.steps
    n_steps = len(steps)
    
    frames = []
    
    for frame_idx in range(n_steps + 1):
        frame_data = []
        
        visible_steps = steps[:frame_idx]
        
        if visible_steps:
            g = nx.DiGraph()
            for s in visible_steps:
                g.add_node(s.name)
            
            for i in range(len(visible_steps) - 1):
                g.add_edge(visible_steps[i].name, visible_steps[i+1].name)
            
            pos = nx.spring_layout(g, seed=42) if len(visible_steps) > 1 else {visible_steps[0].name: (0, 0)}
            
            edge_x, edge_y = [], []
            for u, v in g.edges():
                x0, y0 = pos[u]
                x1, y1 = pos[v]
                edge_x += [x0, x1, None]
                edge_y += [y0, y1, None]
            
            if edge_x:
                frame_data.append(go.Scatter(
                    x=edge_x, y=edge_y,
                    line=dict(width=3, color="rgba(52, 152, 219, 0.6)"),
                    mode="lines",
                    showlegend=False,
                    hoverinfo="none"
                ))
            
            color_scheme = get_agent_color_scheme()
            for step in visible_steps:
                x, y = pos[step.name]
                agent_type = classify_agent_type(step.name)
                colors = color_scheme[agent_type]
                icon = get_skills_icon(agent_type)
                
                frame_data.append(go.Scatter(
                    x=[x], y=[y],
                    mode="markers+text",
                    text=[f"{icon}<br>{step.name}"],
                    textposition="bottom center",
                    marker=dict(
                        size=60,
                        color=colors['primary'],
                        line=dict(width=3, color="white")
                    ),
                    showlegend=False,
                    hovertext=[create_skills_hover_text(step)],
                    hovertemplate="%{hovertext}<extra></extra>"
                ))
        
        frames.append(go.Frame(data=frame_data, name=str(frame_idx)))
    
    fig = go.Figure(
        data=frames[0].data if frames else [],
        frames=frames
    )
    
    fig.update_layout(
        title="🎬 Animated Skills Matching Workflow",
        updatemenus=[{
            "type": "buttons",
            "showactive": False,
            "buttons": [
                {
                    "label": "▶️ Play",
                    "method": "animate",
                    "args": [None, {
                        "frame": {"duration": 1500, "redraw": True},
                        "fromcurrent": True,
                        "transition": {"duration": 500}
                    }]
                },
                {
                    "label": "⏸️ Pause",
                    "method": "animate",
                    "args": [[None], {
                        "frame": {"duration": 0, "redraw": False},
                        "mode": "immediate",
                        "transition": {"duration": 0}
                    }]
                }
            ]
        }],
        sliders=[{
            "steps": [
                {
                    "args": [[f.name], {
                        "frame": {"duration": 300, "redraw": True},
                        "mode": "immediate",
                        "transition": {"duration": 300}
                    }],
                    "label": f"Step {i}",
                    "method": "animate"
                }
                for i, f in enumerate(frames)
            ],
            "active": 0,
            "currentvalue": {"prefix": "Current: "},
            "len": 0.9,
            "x": 0.1,
            "xanchor": "left",
            "y": 0,
            "yanchor": "top"
        }],
        showlegend=False,
        hovermode="closest",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=600,
        margin=dict(l=40, r=40, t=80, b=100)
    )
    
    return fig


def export_workflow_report(trace: WorkflowTrace, style: str = "skills_focused") -> Dict[str, Any]:
    report = {
        'summary': {
            'total_steps': len(trace.steps),
            'total_processing_time': sum(trace.metadata.get('processing_times', [1.0] * len(trace.steps))) if trace.metadata else len(trace.steps),
            'workflow_efficiency': calculate_workflow_efficiency(trace),
            'agent_types': trace.metadata.get('step_types', []) if trace.metadata else []
        },
        'skills_metrics': create_skills_performance_summary(trace),
        'steps': [],
        'performance_metrics': {},
        'visualization_data': {
            'style': style,
            'generated_at': "2024"
        }
    }
    
    for i, step in enumerate(trace.steps):
        step_info = {
            'index': i,
            'name': step.name,
            'agent_type': classify_agent_type(step.name),
            'icon': get_skills_icon(classify_agent_type(step.name)),
            'inputs': step.inputs,
            'outputs': step.outputs,
            'reasoning': step.reasoning,
            'processing_time': trace.metadata.get('processing_times', [1.0] * len(trace.steps))[i] if trace.metadata else 1.0
        }
        report['steps'].append(step_info)
    
    if trace.metadata:
        report['performance_metrics'] = {
            'average_processing_time': sum(trace.metadata.get('processing_times', [])) / len(trace.metadata.get('processing_times', [1])),
            'bottleneck_step': max(enumerate(trace.metadata.get('processing_times', [1])), key=lambda x: x[1])[0] if trace.metadata.get('processing_times') else 0,
            'fastest_step': min(enumerate(trace.metadata.get('processing_times', [1])), key=lambda x: x[1])[0] if trace.metadata.get('processing_times') else 0
        }
    
    return report


def calculate_workflow_efficiency(trace: WorkflowTrace) -> float:
    if not trace.metadata or not trace.metadata.get('processing_times'):
        return 50.0
    
    processing_times = trace.metadata['processing_times']
    
    total_time = sum(processing_times)
    avg_time = total_time / len(processing_times)
    
    variance = sum((t - avg_time) ** 2 for t in processing_times) / len(processing_times)
    
    time_efficiency = max(0, 100 - (total_time * 2))
    variance_penalty = min(variance * 10, 30)
    
    efficiency = max(0, min(100, time_efficiency - variance_penalty))
    
    return efficiency