"""
Tool Argument Fixer Module

This module provides intelligent parameter name matching and fixing for tool calls.
It uses similarity-based matching to handle minor naming discrepancies.
"""

import difflib
from typing import List, Dict, Any, Optional, Tuple
from core.logger import get_logger

ToolSchema = Dict[str, Any]

SIMILARITY_THRESHOLD = 0.2


class ToolArgumentFixer:
    """
    Intelligent tool argument fixer using similarity-based matching.

    This class attempts to fix tool call parameters that may have naming
    mismatches by using string similarity algorithms to map input parameters
    to expected parameters.

    Attributes:
        logger: Logger instance for tracking fix operations
        similarity_threshold: Minimum similarity score for automatic mapping

    Example:
        >>> fixer = ToolArgumentFixer()
        >>> tools = {"search": {"input_schema": {"properties": {"query": {}}, "required": ["query"]}}}
        >>> args = {"q": "test"}  # Wrong parameter name
        >>> fixed_args = fixer.fix(tools, args, "search")
        >>> print(fixed_args)  # {"query": "test"}
    """

    def __init__(self, similarity_threshold: float = SIMILARITY_THRESHOLD):
        """
        Initialize the tool argument fixer.

        Args:
            similarity_threshold: Minimum similarity ratio (0.0-1.0) for automatic parameter mapping
        """
        self.logger = get_logger(__name__)
        self.similarity_threshold = similarity_threshold

    def _get_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate string similarity ratio.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Similarity ratio between 0.0 and 1.0
        """
        return difflib.SequenceMatcher(None, s1, s2).ratio()

    def fix(
        self,
        tools: Dict[str, ToolSchema],
        tool_args: Dict[str, Any],
        tool_name: str
    ) -> Dict[str, Any]:
        """
        Attempt to intelligently fix tool call parameter naming mismatches.

        This method implements a three-stage fixing strategy:
        1. Check if parameters already match (no fix needed)
        2. Try single parameter mapping for simple cases
        3. Apply multi-parameter fuzzy matching for complex cases

        Args:
            tools: Dictionary of all available tool schemas
            tool_args: Input arguments provided by the user/LLM
            tool_name: Name of the tool being called

        Returns:
            Fixed arguments dictionary. Returns original args if fixing fails
            or is not possible.
        """
        tools_schema = tools.get(tool_name)

        if tools_schema is None:
            self.logger.warning(f"Tool '{tool_name}' not found in tools schema")
            return tool_args

        # Get all expected parameter names (required + optional)
        all_expected_params: List[str] = list(
            tools_schema.get("input_schema", {}).get("properties", {}).keys()
        )

        # Extract required parameters
        required_params: List[str] = tools_schema.get("input_schema", {}).get(
            "required", []
        )

        if not all_expected_params or not tool_args:
            return tool_args

        # Stage 1: Check if requirements are already satisfied
        is_required_present = all(param in tool_args for param in required_params)
        if is_required_present:
            self.logger.debug(f"Parameters for '{tool_name}' already match, no fix needed")
            return tool_args

        # Stage 2: Simple single parameter mapping
        if len(required_params) == 1 and len(tool_args) == 1:
            fixed_args = self._try_single_param_mapping(
                required_params[0],
                list(tool_args.keys())[0],
                list(tool_args.values())[0]
            )
            if fixed_args:
                return fixed_args

        # Stage 3: Multi-parameter fuzzy matching
        return self._apply_fuzzy_matching(
            tool_name,
            tool_args,
            all_expected_params,
            required_params
        )

    def _try_single_param_mapping(
        self,
        required_param_name: str,
        input_param_key: str,
        input_param_value: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Attempt to map a single input parameter to a single required parameter.

        Args:
            required_param_name: The expected parameter name
            input_param_key: The provided parameter key
            input_param_value: The provided parameter value

        Returns:
            Fixed arguments dict if mapping succeeds, None otherwise
        """
        if input_param_key == required_param_name:
            return {required_param_name: input_param_value}

        similarity = self._get_similarity(input_param_key, required_param_name)

        if similarity >= self.similarity_threshold:
            fixed_args = {required_param_name: input_param_value}
            self.logger.info(
                f"Single parameter mapping: '{input_param_key}' -> '{required_param_name}' "
                f"(similarity: {similarity:.2f})"
            )
            return fixed_args
        else:
            self.logger.debug(
                f"Single parameter '{input_param_key}' similarity to '{required_param_name}' "
                f"({similarity:.2f}) below threshold ({self.similarity_threshold})"
            )
            return None

    def _apply_fuzzy_matching(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        all_expected_params: List[str],
        required_params: List[str]
    ) -> Dict[str, Any]:
        """
        Apply multi-parameter fuzzy matching to fix parameter names.

        This method performs the following steps:
        1. Pre-process: Match exact parameter names first
        2. Calculate similarity scores for remaining parameters
        3. Greedy matching: Assign best matches first
        4. Validate: Check if all required parameters are satisfied

        Args:
            tool_name: Name of the tool being called
            tool_args: Input arguments provided
            all_expected_params: All expected parameter names
            required_params: Required parameter names

        Returns:
            Fixed arguments if all required params are found, original args otherwise
        """
        fixed_args: Dict[str, Any] = {}
        matched_expected_params: set = set()
        temp_input_args: Dict[str, Any] = {}

        # Stage 3.1: Pre-processing - exact matches first
        for input_key, input_value in tool_args.items():
            if input_key in all_expected_params:
                fixed_args[input_key] = input_value
                matched_expected_params.add(input_key)
            else:
                temp_input_args[input_key] = input_value

        # Stage 3.2: Fuzzy matching for remaining parameters
        remaining_input_keys = list(temp_input_args.keys())
        unmatched_expected_params = [
            p for p in all_expected_params if p not in matched_expected_params
        ]

        if remaining_input_keys and unmatched_expected_params:
            self.logger.debug(
                f"Entering fuzzy matching for tool '{tool_name}': "
                f"{len(remaining_input_keys)} input params, "
                f"{len(unmatched_expected_params)} unmatched expected params"
            )

            # Build potential matches with similarity scores
            potential_matches: List[Tuple[float, str, str]] = []
            # Format: (similarity, expected_param, input_param)

            for input_key in remaining_input_keys:
                for expected_param in unmatched_expected_params:
                    similarity = self._get_similarity(input_key, expected_param)
                    if similarity >= self.similarity_threshold:
                        potential_matches.append((similarity, expected_param, input_key))

            # Sort by similarity (highest first)
            potential_matches.sort(key=lambda x: x[0], reverse=True)

            # Greedy matching: use highest similarity matches first
            used_input_keys = set()

            for similarity, expected_param, input_key in potential_matches:
                # Ensure neither the input key nor expected param has been used
                if (
                    expected_param not in matched_expected_params
                    and input_key not in used_input_keys
                ):
                    fixed_args[expected_param] = temp_input_args[input_key]
                    matched_expected_params.add(expected_param)
                    used_input_keys.add(input_key)

                    self.logger.info(
                        f"Fuzzy match: '{input_key}' -> '{expected_param}' "
                        f"(similarity: {similarity:.2f})"
                    )

        # Stage 3.3: Final validation
        is_required_fixed = all(param in fixed_args for param in required_params)

        if is_required_fixed:
            self.logger.info(
                f"Successfully fixed parameters for tool '{tool_name}': "
                f"{len(fixed_args)} params mapped"
            )
            return fixed_args
        else:
            missing_params = [p for p in required_params if p not in fixed_args]
            self.logger.warning(
                f"Unable to fix parameters for tool '{tool_name}'. "
                f"Missing required params: {missing_params}. "
                f"Returning original args: {list(tool_args.keys())}"
            )
            return tool_args


# Global instance for convenient access
_default_fixer = ToolArgumentFixer()


def fix_tool_args(
    tools: Dict[str, ToolSchema],
    tool_args: Dict[str, Any],
    tool_name: str
) -> Dict[str, Any]:
    """
    Convenience function to fix tool argument naming mismatches.

    This is the main interface for the module. It uses a global
    ToolArgumentFixer instance to attempt to fix parameter names.

    Args:
        tools: Dictionary of all available tool schemas
        tool_args: Input arguments provided by the user/LLM
        tool_name: Name of the tool being called

    Returns:
        Fixed arguments dictionary. Returns original args if fixing fails.

    Example:
        >>> from core.tool_hash import fix_tool_args
        >>> tools = {"search": {"input_schema": {"properties": {"query": {}}, "required": ["query"]}}}
        >>> args = {"q": "python tutorial"}
        >>> fixed = fix_tool_args(tools, args, "search")
        >>> print(fixed)  # {"query": "python tutorial"}
    """
    return _default_fixer.fix(tools, tool_args, tool_name)


__all__ = [
    "ToolArgumentFixer",
    "fix_tool_args",
    "SIMILARITY_THRESHOLD",
]
