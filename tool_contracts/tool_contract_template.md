# Tool Contract Template

## 1. Purpose

Tools are deterministic, narrow components that micro agents and the orchestrator call to perform specific computations or checks. They encapsulate business logic, data validation, and system interactions in a predictable, testable manner. Unlike agents, tools do not make autonomous decisions or maintain state across invocations.

This template ensures that every tool has a clear contract so that agents and evaluation frameworks can rely on it. By standardizing how tools are documented, we enable consistent tool selection, error handling, and observability across the WMS system.

## 2. Summary

Provide a short description of what the tool does in one or two sentences. This should be clear enough for an agent or engineer to understand the tool's primary function without reading the full contract.

## 3. Inputs

Document all inputs in a table with the following columns:

| Field Name | Type | Description | Required/Optional | Example |
|------------|------|-------------|-------------------|---------|
| ...        | ...  | ...         | ...               | ...     |

**Guidance for documenting inputs:**

- **Units of measure**: Explicitly state units (e.g., kilograms, cubic meters, minutes) for any numeric fields
- **Identifiers and keys**: Specify the format and source of identifiers (e.g., SKU format, location codes, order IDs)
- **Expected ranges**: Document valid ranges for numeric inputs (e.g., quantity must be > 0, temperature range)
- **Default values**: If any inputs have defaults, state them clearly and when they apply

## 4. Outputs

Document all outputs in a table with the following columns:

| Field Name | Type | Description | Example |
|------------|------|-------------|---------|
| ...        | ...  | ...         | ...     |

**Guidance for documenting outputs:**

- **Required vs Optional**: Clearly mark which fields are always present versus conditionally present
- **Machine-friendly codes**: Include status codes, error codes, or other structured values that agents can parse
- **Human-readable labels**: Provide descriptive text or labels alongside codes for debugging and logging

## 5. Deterministic Guarantees

Document the deterministic behavior of the tool:

- **Strict determinism**: State whether the tool produces identical outputs for identical inputs (allowing for controlled randomness)
- **Controlled randomness**: If the tool uses randomness (e.g., for sampling or tie-breaking), describe how it is seeded or logged to ensure reproducibility
- **Performance expectations**: Document any performance guarantees or limits (e.g., maximum execution time, throughput) that are important for orchestration decisions

## 6. Preconditions

List all conditions that must be true before calling the tool:

- **Data conditions**: Required data state (e.g., inventory records must exist, order must be in a specific status)
- **Data freshness**: Dependencies on upstream data freshness or quality (e.g., inventory counts must be updated within last hour)
- **Permissions and configuration**: Any required permissions, feature flags, or system configuration that must exist

## 7. Postconditions

Describe what is guaranteed after the tool runs successfully:

- **Output constraints**: Constraints that outputs will always respect (e.g., quantities never negative, status codes from defined set)
- **Invariants**: System or data invariants that should never be violated by the tool's execution
- **Side effects**: Any side effects (if they exist) and how they are controlled (e.g., audit logs written, cache updates)

## 8. Constraints and Safety Checks

Document the business and safety rules enforced by the tool:

- **Internal enforcement**: Which business or safety rules the tool enforces internally (e.g., weight limits, hazardous material restrictions)
- **External assumptions**: Which rules are assumed to be enforced by the agent or other components (e.g., agent validates permissions before calling)
- **Hard limits**: Any hard limits or thresholds the tool will never exceed, even if requested (e.g., maximum pick quantity per container)

## 9. Error Handling and Failure Modes

List all error conditions in a structured format:

| Error Code/Category | Typical Causes | Agent Response |
|---------------------|----------------|----------------|
| ...                 | ...            | ...            |

**Guidance for documenting errors:**

- **Error codes or categories**: Use consistent error codes or categories that agents can programmatically handle
- **Typical causes**: Describe common scenarios that lead to each error
- **Agent response**: Specify how agents should respond (e.g., retry with backoff, escalate to human, abort workflow, use fallback)

## 10. Observability

Define the logging and metrics requirements:

- **Required logs**: Minimum logging that must be emitted for inputs, outputs, errors, and timing
- **Metrics**: Key metrics the tool should expose (e.g., execution time, success rate, input validation failures)
- **Traceability identifiers**: Any identifiers required for traceability back to orders, locations, workers, or other business entities (e.g., order ID, picker ID, timestamp)

## 11. Example Usage

Provide a short, representative example:

```python
# Example call
result = tool_name(
    input_field_1="example_value",
    input_field_2=42
)

# Example output
{
    "output_field_1": "result_value",
    "output_field_2": 100,
    "status": "success"
}
```

**Note on agent interpretation**: Briefly describe how a micro agent would interpret the result (e.g., "Agent checks status field; if 'success', proceeds to next step; if 'error', handles according to error code").

