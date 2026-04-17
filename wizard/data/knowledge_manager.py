"""
Knowledge Manager Module

This module provides utilities for managing the local knowledge base,
including importing, exporting, and updating knowledge facts.
"""

import json
import csv
import sqlite3
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class KnowledgeManager:
    """
    Manager for the local knowledge base operations
    """
    
    def __init__(self, db_path: str = "wizard/data/knowledge.db"):
        self.db_path = db_path
    
    def import_knowledge_from_json(self, json_file: str) -> bool:
        """
        Import knowledge facts from a JSON file
        
        Args:
            json_file: Path to JSON file containing knowledge facts
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                imported_count = 0
                for category, facts in data.items():
                    for fact in facts:
                        cursor.execute('''
                            INSERT OR REPLACE INTO facts (category, question, answer, confidence)
                            VALUES (?, ?, ?, ?)
                        ''', (
                            category,
                            fact.get("question", ""),
                            fact.get("answer", ""),
                            fact.get("confidence", 1.0)
                        ))
                        imported_count += 1
                
                conn.commit()
                logger.info(f"Imported {imported_count} facts from {json_file}")
                return True
                
        except Exception as e:
            logger.error(f"Error importing knowledge from JSON: {e}")
            return False
    
    def export_knowledge_to_json(self, json_file: str, category: str = None) -> bool:
        """
        Export knowledge facts to a JSON file
        
        Args:
            json_file: Path to output JSON file
            category: Optional category filter
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if category:
                    cursor.execute('''
                        SELECT category, question, answer, confidence
                        FROM facts 
                        WHERE category = ?
                        ORDER BY category, question
                    ''', (category,))
                else:
                    cursor.execute('''
                        SELECT category, question, answer, confidence
                        FROM facts 
                        ORDER BY category, question
                    ''')
                
                # Organize by category
                knowledge_data = {}
                for row in cursor.fetchall():
                    cat, question, answer, confidence = row
                    if cat not in knowledge_data:
                        knowledge_data[cat] = []
                    
                    knowledge_data[cat].append({
                        "question": question,
                        "answer": answer,
                        "confidence": confidence
                    })
                
                # Write to JSON file
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(knowledge_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Exported knowledge to {json_file}")
                return True
                
        except Exception as e:
            logger.error(f"Error exporting knowledge to JSON: {e}")
            return False
    
    def import_knowledge_from_csv(self, csv_file: str) -> bool:
        """
        Import knowledge facts from a CSV file
        Expected columns: category, question, answer, confidence
        
        Args:
            csv_file: Path to CSV file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    imported_count = 0
                    for row in reader:
                        cursor.execute('''
                            INSERT OR REPLACE INTO facts (category, question, answer, confidence)
                            VALUES (?, ?, ?, ?)
                        ''', (
                            row.get("category", "general"),
                            row.get("question", ""),
                            row.get("answer", ""),
                            float(row.get("confidence", 1.0))
                        ))
                        imported_count += 1
                    
                    conn.commit()
                    logger.info(f"Imported {imported_count} facts from {csv_file}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error importing knowledge from CSV: {e}")
            return False
    
    def export_knowledge_to_csv(self, csv_file: str, category: str = None) -> bool:
        """
        Export knowledge facts to a CSV file
        
        Args:
            csv_file: Path to output CSV file
            category: Optional category filter
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if category:
                    cursor.execute('''
                        SELECT category, question, answer, confidence
                        FROM facts 
                        WHERE category = ?
                        ORDER BY category, question
                    ''', (category,))
                else:
                    cursor.execute('''
                        SELECT category, question, answer, confidence
                        FROM facts 
                        ORDER BY category, question
                    ''')
                
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["category", "question", "answer", "confidence"])
                    
                    for row in cursor.fetchall():
                        writer.writerow(row)
                
                logger.info(f"Exported knowledge to {csv_file}")
                return True
                
        except Exception as e:
            logger.error(f"Error exporting knowledge to CSV: {e}")
            return False
    
    def add_bulk_facts(self, facts: List[Dict[str, Any]]) -> int:
        """
        Add multiple facts to the knowledge base
        
        Args:
            facts: List of fact dictionaries with keys: category, question, answer, confidence
            
        Returns:
            Number of facts successfully added
        """
        added_count = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for fact in facts:
                    try:
                        cursor.execute('''
                            INSERT INTO facts (category, question, answer, confidence)
                            VALUES (?, ?, ?, ?)
                        ''', (
                            fact.get("category", "general"),
                            fact.get("question", ""),
                            fact.get("answer", ""),
                            fact.get("confidence", 1.0)
                        ))
                        added_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to add fact: {fact.get('question', 'Unknown')}: {e}")
                
                conn.commit()
                logger.info(f"Added {added_count} facts to knowledge base")
                
        except Exception as e:
            logger.error(f"Error adding bulk facts: {e}")
        
        return added_count
    
    def update_fact(self, fact_id: int, **kwargs) -> bool:
        """
        Update an existing fact
        
        Args:
            fact_id: ID of the fact to update
            **kwargs: Fields to update (category, question, answer, confidence)
            
        Returns:
            True if successful, False otherwise
        """
        if not kwargs:
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build update query
                set_clauses = []
                values = []
                
                for field in ["category", "question", "answer", "confidence"]:
                    if field in kwargs:
                        set_clauses.append(f"{field} = ?")
                        values.append(kwargs[field])
                
                if set_clauses:
                    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                    query = f"UPDATE facts SET {', '.join(set_clauses)} WHERE id = ?"
                    values.append(fact_id)
                    
                    cursor.execute(query, values)
                    conn.commit()
                    
                    if cursor.rowcount > 0:
                        logger.info(f"Updated fact ID {fact_id}")
                        return True
                    else:
                        logger.warning(f"No fact found with ID {fact_id}")
                        return False
                
        except Exception as e:
            logger.error(f"Error updating fact: {e}")
            return False
    
    def delete_fact(self, fact_id: int) -> bool:
        """
        Delete a fact from the knowledge base
        
        Args:
            fact_id: ID of the fact to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM facts WHERE id = ?", (fact_id,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Deleted fact ID {fact_id}")
                    return True
                else:
                    logger.warning(f"No fact found with ID {fact_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error deleting fact: {e}")
            return False
    
    def get_categories(self) -> List[str]:
        """Get all categories in the knowledge base"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT category FROM facts ORDER BY category")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    def get_facts_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all facts in a specific category"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, question, answer, confidence, created_at, updated_at
                    FROM facts 
                    WHERE category = ?
                    ORDER BY question
                ''', (category,))
                
                facts = []
                for row in cursor.fetchall():
                    facts.append({
                        "id": row[0],
                        "question": row[1],
                        "answer": row[2],
                        "confidence": row[3],
                        "created_at": row[4],
                        "updated_at": row[5]
                    })
                
                return facts
                
        except Exception as e:
            logger.error(f"Error getting facts by category: {e}")
            return []
    
    def search_facts_advanced(self, query: str, category: str = None, 
                            min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """
        Advanced search for facts with filters
        
        Args:
            query: Search query
            category: Optional category filter
            min_confidence: Minimum confidence score
            
        Returns:
            List of matching facts
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                base_query = '''
                    SELECT id, category, question, answer, confidence, created_at, updated_at
                    FROM facts 
                    WHERE confidence >= ? AND (LOWER(question) LIKE ? OR LOWER(answer) LIKE ?)
                '''
                params = [min_confidence, f"%{query.lower()}%", f"%{query.lower()}%"]
                
                if category:
                    base_query += " AND category = ?"
                    params.append(category)
                
                base_query += " ORDER BY confidence DESC, question"
                
                cursor.execute(base_query, params)
                
                facts = []
                for row in cursor.fetchall():
                    facts.append({
                        "id": row[0],
                        "category": row[1],
                        "question": row[2],
                        "answer": row[3],
                        "confidence": row[4],
                        "created_at": row[5],
                        "updated_at": row[6]
                    })
                
                return facts
                
        except Exception as e:
            logger.error(f"Error in advanced search: {e}")
            return []
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total facts
                cursor.execute("SELECT COUNT(*) FROM facts")
                total_facts = cursor.fetchone()[0]
                
                # Facts by category
                cursor.execute('''
                    SELECT category, COUNT(*) as count 
                    FROM facts 
                    GROUP BY category 
                    ORDER BY count DESC
                ''')
                category_counts = cursor.fetchall()
                
                # Average confidence
                cursor.execute("SELECT AVG(confidence) FROM facts")
                avg_confidence = cursor.fetchone()[0] or 0.0
                
                # Recent additions
                cursor.execute('''
                    SELECT COUNT(*) FROM facts 
                    WHERE created_at > datetime('now', '-7 days')
                ''')
                recent_additions = cursor.fetchone()[0]
                
                return {
                    "total_facts": total_facts,
                    "categories": dict(category_counts),
                    "average_confidence": round(avg_confidence, 2),
                    "recent_additions_7d": recent_additions
                }
                
        except Exception as e:
            logger.error(f"Error getting knowledge stats: {e}")
            return {}
    
    def cleanup_low_confidence_facts(self, min_confidence: float = 0.3) -> int:
        """
        Remove facts with confidence below threshold
        
        Args:
            min_confidence: Minimum confidence to keep
            
        Returns:
            Number of facts removed
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM facts WHERE confidence < ?", (min_confidence,))
                conn.commit()
                
                removed_count = cursor.rowcount
                logger.info(f"Removed {removed_count} low-confidence facts")
                return removed_count
                
        except Exception as e:
            logger.error(f"Error cleaning up facts: {e}")
            return 0