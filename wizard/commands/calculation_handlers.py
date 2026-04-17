"""
Calculation Handlers Module

This module handles mathematical calculations, unit conversions, and time/date operations
for the Wizard voice assistant.
"""

import re
import math
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from .command_router import Command, Response

logger = logging.getLogger(__name__)


class CalculationHandlers:
    """Handles mathematical calculations and unit conversions"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.date_formats = config.get('date_formats', {
            'default': '%Y-%m-%d',
            'us': '%m/%d/%Y',
            'eu': '%d/%m/%Y',
            'long': '%A, %B %d, %Y'
        })
        self.time_formats = config.get('time_formats', {
            'default': '%H:%M:%S',
            '12hour': '%I:%M:%S %p',
            'short': '%H:%M'
        })
        
        # Unit conversion factors (to base units)
        self.length_conversions = {
            'mm': 0.001, 'millimeter': 0.001, 'millimeters': 0.001,
            'cm': 0.01, 'centimeter': 0.01, 'centimeters': 0.01,
            'm': 1.0, 'meter': 1.0, 'meters': 1.0, 'metre': 1.0, 'metres': 1.0,
            'km': 1000.0, 'kilometer': 1000.0, 'kilometers': 1000.0, 'kilometre': 1000.0, 'kilometres': 1000.0,
            'in': 0.0254, 'inch': 0.0254, 'inches': 0.0254,
            'ft': 0.3048, 'foot': 0.3048, 'feet': 0.3048,
            'yd': 0.9144, 'yard': 0.9144, 'yards': 0.9144,
            'mi': 1609.344, 'mile': 1609.344, 'miles': 1609.344
        }
        
        self.weight_conversions = {
            'mg': 0.000001, 'milligram': 0.000001, 'milligrams': 0.000001,
            'g': 0.001, 'gram': 0.001, 'grams': 0.001,
            'kg': 1.0, 'kilogram': 1.0, 'kilograms': 1.0,
            'oz': 0.0283495, 'ounce': 0.0283495, 'ounces': 0.0283495,
            'lb': 0.453592, 'pound': 0.453592, 'pounds': 0.453592,
            'st': 6.35029, 'stone': 6.35029, 'stones': 6.35029,
            't': 1000.0, 'ton': 1000.0, 'tons': 1000.0, 'tonne': 1000.0, 'tonnes': 1000.0
        }
        
        self.temperature_conversions = {
            'celsius': 'C', 'c': 'C', 'centigrade': 'C',
            'fahrenheit': 'F', 'f': 'F',
            'kelvin': 'K', 'k': 'K'
        }
        
        # Basic currency rates (should be updated from external source in production)
        self.currency_rates = {
            'USD': 1.0,  # Base currency
            'EUR': 0.85,
            'GBP': 0.73,
            'JPY': 110.0,
            'CAD': 1.25,
            'AUD': 1.35,
            'CHF': 0.92,
            'CNY': 6.45,
            'INR': 74.5
        }
    
    def handle_calculate(self, command: Command) -> Response:
        """Handle mathematical calculation requests"""
        try:
            query = command.entities.get('query', '').strip()
            if not query:
                return Response(
                    text="I need a mathematical expression to calculate. For example, 'calculate 2 plus 3' or 'what is 15 times 7'.",
                    action_taken=False
                )
            
            # Clean and parse the mathematical expression
            result = self._evaluate_math_expression(query)
            
            if result is not None:
                return Response(
                    text=f"The result is {result}",
                    action_taken=True,
                    context_updates={'last_calculation': result}
                )
            else:
                return Response(
                    text="I couldn't understand that mathematical expression. Please try rephrasing it.",
                    action_taken=False
                )
                
        except Exception as e:
            logger.error(f"Error in calculation: {e}")
            return Response(
                text="Sorry, I encountered an error while calculating that.",
                error_message=str(e)
            )
    
    def handle_unit_conversion(self, command: Command) -> Response:
        """Handle unit conversion requests"""
        try:
            query = command.entities.get('query', '').strip()
            if not query:
                return Response(
                    text="Please specify what you'd like to convert. For example, 'convert 5 feet to meters'.",
                    action_taken=False
                )
            
            result = self._convert_units(query)
            
            if result:
                return Response(
                    text=result,
                    action_taken=True
                )
            else:
                return Response(
                    text="I couldn't understand that conversion request. Please try rephrasing it.",
                    action_taken=False
                )
                
        except Exception as e:
            logger.error(f"Error in unit conversion: {e}")
            return Response(
                text="Sorry, I encountered an error while converting those units.",
                error_message=str(e)
            )
    
    def handle_what_time(self, command: Command) -> Response:
        """Handle time requests"""
        try:
            format_type = command.entities.get('format', 'default')
            time_format = self.time_formats.get(format_type, self.time_formats['default'])
            
            current_time = datetime.now()
            formatted_time = current_time.strftime(time_format)
            
            return Response(
                text=f"The current time is {formatted_time}",
                action_taken=True,
                context_updates={'current_time': formatted_time}
            )
            
        except Exception as e:
            logger.error(f"Error getting time: {e}")
            return Response(
                text="Sorry, I couldn't get the current time.",
                error_message=str(e)
            )
    
    def handle_what_date(self, command: Command) -> Response:
        """Handle date requests"""
        try:
            format_type = command.entities.get('format', 'default')
            date_format = self.date_formats.get(format_type, self.date_formats['default'])
            
            current_date = datetime.now()
            formatted_date = current_date.strftime(date_format)
            
            return Response(
                text=f"Today's date is {formatted_date}",
                action_taken=True,
                context_updates={'current_date': formatted_date}
            )
            
        except Exception as e:
            logger.error(f"Error getting date: {e}")
            return Response(
                text="Sorry, I couldn't get the current date.",
                error_message=str(e)
            )
    
    def _evaluate_math_expression(self, expression: str) -> Optional[float]:
        """Safely evaluate a mathematical expression"""
        try:
            # Convert natural language to mathematical operators
            expression = self._parse_natural_language_math(expression)
            
            # Remove any non-mathematical characters for safety
            allowed_chars = set('0123456789+-*/().^ ')
            expression = ''.join(c for c in expression if c in allowed_chars)
            
            # Replace ^ with ** for Python exponentiation
            expression = expression.replace('^', '**')
            
            # Evaluate the expression safely
            # Only allow basic mathematical operations
            allowed_names = {
                "__builtins__": {},
                "abs": abs,
                "round": round,
                "pow": pow,
                "sqrt": math.sqrt,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "log": math.log,
                "pi": math.pi,
                "e": math.e
            }
            
            result = eval(expression, allowed_names, {})
            return round(result, 6) if isinstance(result, float) else result
            
        except Exception as e:
            logger.error(f"Error evaluating expression '{expression}': {e}")
            return None
    
    def _parse_natural_language_math(self, text: str) -> str:
        """Convert natural language math to mathematical expression"""
        text = text.lower()
        
        # Replace word operators with symbols
        replacements = {
            ' plus ': ' + ',
            ' add ': ' + ',
            ' added to ': ' + ',
            ' minus ': ' - ',
            ' subtract ': ' - ',
            ' subtracted from ': ' - ',
            ' times ': ' * ',
            ' multiplied by ': ' * ',
            ' multiply ': ' * ',
            ' divided by ': ' / ',
            ' divide ': ' / ',
            ' to the power of ': ' ** ',
            ' squared ': ' ** 2',
            ' cubed ': ' ** 3'
        }
        
        for word, symbol in replacements.items():
            text = text.replace(word, symbol)
        
        # Handle percentage calculations
        if ' percent of ' in text:
            text = re.sub(r'(\d+(?:\.\d+)?)\s+percent\s+of\s+(\d+(?:\.\d+)?)', r'(\1 / 100) * \2', text)
        elif ' percentage ' in text:
            text = text.replace(' percentage ', ' / 100 ')
        elif ' percent ' in text:
            text = text.replace(' percent ', ' / 100 ')
        
        # Handle special functions
        if 'square root of' in text:
            text = re.sub(r'square root of (\d+(?:\.\d+)?)', r'sqrt(\1)', text)
        
        return text
    
    def _convert_units(self, query: str) -> Optional[str]:
        """Convert between different units"""
        query = query.lower()
        
        # Parse conversion request
        # Pattern: "convert X unit1 to unit2" or "X unit1 to unit2" or "X unit1 in unit2"
        patterns = [
            r'convert\s+(\d+(?:\.\d+)?)\s+(\w+)\s+to\s+(\w+)',
            r'(\d+(?:\.\d+)?)\s+(\w+)\s+to\s+(\w+)',
            r'(\d+(?:\.\d+)?)\s+(\w+)\s+in\s+(\w+)',
            r'how\s+many\s+(\w+)\s+in\s+(\d+(?:\.\d+)?)\s+(\w+)',
            r'how\s+many\s+(\w+)\s+are\s+in\s+(\d+(?:\.\d+)?)\s+(\w+)'
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, query)
            if match:
                if i >= 3:  # Last two patterns have different group order
                    unit_to = match.group(1)
                    value = float(match.group(2))
                    unit_from = match.group(3)
                else:
                    value = float(match.group(1))
                    unit_from = match.group(2)
                    unit_to = match.group(3)
                
                # Try different conversion types
                result = self._convert_length(value, unit_from, unit_to)
                if result is not None:
                    return f"{value} {unit_from} equals {result:.4f} {unit_to}"
                
                result = self._convert_weight(value, unit_from, unit_to)
                if result is not None:
                    return f"{value} {unit_from} equals {result:.4f} {unit_to}"
                
                result = self._convert_temperature(value, unit_from, unit_to)
                if result is not None:
                    return f"{value}° {unit_from.upper()} equals {result:.2f}° {unit_to.upper()}"
                
                result = self._convert_currency(value, unit_from.upper(), unit_to.upper())
                if result is not None:
                    return f"{value} {unit_from.upper()} equals {result:.2f} {unit_to.upper()}"
        
        return None
    
    def _convert_length(self, value: float, from_unit: str, to_unit: str) -> Optional[float]:
        """Convert between length units"""
        if from_unit in self.length_conversions and to_unit in self.length_conversions:
            # Convert to meters, then to target unit
            meters = value * self.length_conversions[from_unit]
            result = meters / self.length_conversions[to_unit]
            return result
        return None
    
    def _convert_weight(self, value: float, from_unit: str, to_unit: str) -> Optional[float]:
        """Convert between weight units"""
        if from_unit in self.weight_conversions and to_unit in self.weight_conversions:
            # Convert to kilograms, then to target unit
            kilograms = value * self.weight_conversions[from_unit]
            result = kilograms / self.weight_conversions[to_unit]
            return result
        return None
    
    def _convert_temperature(self, value: float, from_unit: str, to_unit: str) -> Optional[float]:
        """Convert between temperature units"""
        from_unit = self.temperature_conversions.get(from_unit, from_unit.upper())
        to_unit = self.temperature_conversions.get(to_unit, to_unit.upper())
        
        if from_unit == to_unit:
            return value
        
        # Convert to Celsius first
        if from_unit == 'F':
            celsius = (value - 32) * 5/9
        elif from_unit == 'K':
            celsius = value - 273.15
        elif from_unit == 'C':
            celsius = value
        else:
            return None
        
        # Convert from Celsius to target
        if to_unit == 'F':
            return celsius * 9/5 + 32
        elif to_unit == 'K':
            return celsius + 273.15
        elif to_unit == 'C':
            return celsius
        
        return None
    
    def _convert_currency(self, value: float, from_currency: str, to_currency: str) -> Optional[float]:
        """Convert between currencies using basic rates"""
        if from_currency in self.currency_rates and to_currency in self.currency_rates:
            # Convert to USD, then to target currency
            usd_value = value / self.currency_rates[from_currency]
            result = usd_value * self.currency_rates[to_currency]
            return result
        return None


def register_calculation_handlers(router, config: Dict[str, Any]) -> None:
    """Register all calculation handlers with the command router"""
    handlers = CalculationHandlers(config)
    
    # Register handlers
    router.register_handler("calculate", handlers.handle_calculate)
    router.register_handler("unit_conversion", handlers.handle_unit_conversion)
    router.register_handler("what_time", handlers.handle_what_time)
    router.register_handler("what_date", handlers.handle_what_date)
    
    logger.info("Registered calculation handlers")