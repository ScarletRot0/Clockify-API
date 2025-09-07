
from pydantic import BaseModel
from typing import Optional, List, Dict

class TimeInterval(BaseModel):
    start: str
    end: Optional[str]
    duration: Optional[str]
    timeZone: str
    offsetStart: int
    offsetEnd: Optional[int]
    zonedStart: Optional[str]
    zonedEnd: Optional[str]

class ProjectInfo(BaseModel):
    id: str
    name: str
    clientId: Optional[str]
    workspaceId: str
    billable: bool
    clientName: Optional[str]

class TaskInfo(BaseModel):
    id: str
    name: str
    status: str
    projectId: str

class UserInfo(BaseModel):
    id: str
    name: str
    status: str

class WebhookEvent(BaseModel):
    id: str
    description: Optional[str]
    userId: str
    projectId: Optional[str]
    workspaceId: str
    currentlyRunning: bool
    timeInterval: TimeInterval
    project: Optional[ProjectInfo]
    task: Optional[TaskInfo]
    user: UserInfo
    tags: Optional[List[str]] = []
