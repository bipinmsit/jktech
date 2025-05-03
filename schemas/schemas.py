from pydantic import BaseModel
from typing import Optional

class MailBase(BaseModel):
    
    pk_email_uuid: str
    usermail: str
    fk_curr_stage_id: int
    email_outlook_id: str
    
    class Config:
        """Pydantic config class"""
        from_attributes = True
        
class MailOut(BaseModel):
    pk_email_uuid: str
    usermail: str
    fk_curr_stage_id: int
    email_outlook_id: str
    email_queue_message_id: str
    subject: str
    quote_details: str
    
    
    class Config:
        """Pydantic config class"""
        from_attributes = True
    
class PageBase(BaseModel):
    page_name: str
    fk_doc_id: str
    uploaded_folder_path: str
    
    class Config:
        """Pydantic config class"""
        from_attributes = True
    
class PageOut(BaseModel):
    pk_page: str
    page_name: str
    fk_doc_id: str
    uploaded_folder_path: str
    
    class Config:
        """Pydantic config class"""
        from_attributes = True
 
    
class WorkflowBase(BaseModel):
    fk_mail_id: str
    reason_stage_change: Optional[str]
    transition_stage_id: int
    
    class Config:
        """Pydantic config class"""
        from_attributes = True
    
    
class WorkflowOut(BaseModel):
    pk_workflow: str
    fk_mail_id: int
    reason_stage_change: Optional[str]
    transition_stage_id: int
    
    class Config:
        """Pydantic config class"""
        from_attributes = True
    
    
class ExceptioBase(BaseModel):
    fk_mail_id: str
    message: str
    
    class Config:
        """Pydantic config class"""
        from_attributes = True
        
      
class ExceptionOut(BaseModel):
    pk_exception: str
    fk_mail_id: str
    message: str
    
    class Config:
        """Pydantic config class"""
        from_attributes = True 
        
class StageBase(BaseModel):
    stage_name: str
    
    class Config:
        """Pydantic config class"""
        from_attributes = True 
     
class StageOut(BaseModel):
    pk_stage_id: int
    stage_name: str
    
    class Config:
        """Pydantic config class"""
        from_attributes = True
    
    
    
class DocumentBase(BaseModel):
    doc_name: str
    fk_mail_id: str
    
    class Config:
        """Pydantic config class"""
        from_attributes = True
        
class DocumentOut(BaseModel):
    pk_document_id: str
    doc_name: str
    fk_mail_id: str

    