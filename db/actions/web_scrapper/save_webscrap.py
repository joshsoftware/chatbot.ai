from db.schema import Orgnization
from db.index import UserSession


def save_webscrap(data: dict, session: UserSession) -> Orgnization:   
    org_data = Orgnization(
        websiteUrl=data['websiteUrl'],
        websiteDepth=data['websiteDepth'],
        websiteMaxNumberOfPages=data['websiteMaxNumberOfPages'],
        lastScrapedDate=data['lastScrapedDate'],
        filePath=data['filePath']
    )
    
    session.add(org_data)
    session.commit()
    session.refresh(org_data)
    return org_data
