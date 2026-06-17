from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    # to ensure incoming queries are not empty
    query: str = Field(min_length=1, description="The user question targeting the AWS contract documentation.")

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: list[str]
    latency_seconds: float

class AnalyticsSummary(BaseModel):
    total_queries: int
    most_frequent_queries: list[dict]
    unanswered_queries_count: int
    average_latency_seconds: float

    class Config:
        from_attributes = True