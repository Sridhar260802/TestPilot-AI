from pydantic import BaseModel

class WebsiteTestRequest(BaseModel):
    url: str


class WebsiteTestResponse(BaseModel):
    id: int
    url: str
    status_code: int
    response_time: float
    ssl_status: str
    test_status: str

    class Config:
        from_attributes = True