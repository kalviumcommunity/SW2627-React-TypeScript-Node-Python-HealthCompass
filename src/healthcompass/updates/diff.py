"""Diff generation utility for comparing document versions."""

from typing import List, Tuple
import difflib


class DiffChange:
    """Represents a single change in a diff."""
    
    def __init__(self, type: str, content: str, position: int = 0):
        self.type = type  # 'added', 'removed', 'unchanged'
        self.content = content
        self.position = position
    
    def to_dict(self) -> dict:
        return {
            'type': self.type,
            'content': self.content,
            'position': self.position,
        }


def generate_text_diff(previous: str, new: str) -> List[DiffChange]:
    """
    Generate a word-level diff between two text strings.
    
    Args:
        previous: The previous version text
        new: The new version text
    
    Returns:
        List of DiffChange objects representing the differences
    """
    # Split into words for more granular diff
    previous_words = previous.split()
    new_words = new.split()
    
    # Use difflib to get opcodes
    matcher = difflib.SequenceMatcher(None, previous_words, new_words)
    opcodes = matcher.get_opcodes()
    
    changes = []
    position = 0
    
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == 'equal':
            # Unchanged text
            words = previous_words[i1:i2]
            if words:
                changes.append(DiffChange('unchanged', ' '.join(words), position))
                position += len(words)
        elif tag == 'replace':
            # Removed then added
            removed_words = previous_words[i1:i2]
            added_words = new_words[j1:j2]
            if removed_words:
                changes.append(DiffChange('removed', ' '.join(removed_words), position))
            if added_words:
                changes.append(DiffChange('added', ' '.join(added_words), position))
            position += max(len(removed_words), len(added_words))
        elif tag == 'delete':
            # Removed text
            removed_words = previous_words[i1:i2]
            if removed_words:
                changes.append(DiffChange('removed', ' '.join(removed_words), position))
        elif tag == 'insert':
            # Added text
            added_words = new_words[j1:j2]
            if added_words:
                changes.append(DiffChange('added', ' '.join(added_words), position))
                position += len(added_words)
    
    return changes


def generate_line_diff(previous: str, new: str) -> List[dict]:
    """
    Generate a line-level diff between two text strings.
    
    Args:
        previous: The previous version text
        new: The new version text
    
    Returns:
        List of dicts with 'type', 'content', and 'line_number'
    """
    previous_lines = previous.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        previous_lines,
        new_lines,
        lineterm='',
        fromfile='previous',
        tofile='new',
    )
    
    changes = []
    line_number = 0
    
    for line in diff:
        if line.startswith('@@'):
            # Parse hunk header for line numbers
            continue
        elif line.startswith('-'):
            changes.append({
                'type': 'removed',
                'content': line[1:],
                'line_number': line_number,
            })
        elif line.startswith('+'):
            changes.append({
                'type': 'added',
                'content': line[1:],
                'line_number': line_number,
            })
        elif line.startswith(' '):
            changes.append({
                'type': 'unchanged',
                'content': line[1:],
                'line_number': line_number,
            })
            line_number += 1
    
    return changes


def format_diff_html(changes: List[DiffChange]) -> str:
    """
    Format diff changes as HTML with color coding.
    
    Args:
        changes: List of DiffChange objects
    
    Returns:
        HTML string with styled diff
    """
    html_parts = []
    
    for change in changes:
        if change.type == 'added':
            html_parts.append(f'<span class="diff-added">{change.content}</span>')
        elif change.type == 'removed':
            html_parts.append(f'<span class="diff-removed">{change.content}</span>')
        else:
            html_parts.append(f'<span class="diff-unchanged">{change.content}</span>')
    
    return ' '.join(html_parts)


def get_diff_summary(previous: str, new: str) -> dict:
    """
    Get a summary of the differences between two texts.
    
    Args:
        previous: The previous version text
        new: The new version text
    
    Returns:
        Dict with statistics about the diff
    """
    changes = generate_text_diff(previous, new)
    
    added_count = sum(1 for c in changes if c.type == 'added')
    removed_count = sum(1 for c in changes if c.type == 'removed')
    unchanged_count = sum(1 for c in changes if c.type == 'unchanged')
    
    total_changes = added_count + removed_count
    
    return {
        'total_changes': total_changes,
        'added_count': added_count,
        'removed_count': removed_count,
        'unchanged_count': unchanged_count,
        'change_percentage': (total_changes / len(changes) * 100) if changes else 0,
    }
