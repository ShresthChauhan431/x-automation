import os
import yaml
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, SecretStr
from typing import Literal

# --- Data Models ---
class AccountCredentials(BaseModel):
    api_key: str
    api_secret: str
    access_token: str
    access_secret: str

class PersonalityConfig(BaseModel):
    bio: str
    style: str
    topics: List[str]

class AccountConfig(BaseModel):
    id: str
    enabled: bool = True
    handle: str
    niche: str
    proxy_url: Optional[str] = None
    credentials: AccountCredentials
    personality: PersonalityConfig

# --- Main System Config ---
class SystemConfig(BaseModel):
    # Global Services
    GEMINI_API_KEY: str = Field(default="", description="Gemini API Key")
    
    # Paths
    DATA_DIR: str = Field(default="./data", description="Path to persistence directory")
    ACCOUNTS_FILE: str = Field(default="accounts.yaml", description="Path to accounts config")
    
    # Safe Launch Protocol
    LAUNCH_MODE: Literal["SHADOW", "APPROVAL", "AUTONOMOUS"] = Field(
        default="SHADOW", 
        description="Current operational mode"
    )
    
    # Global Defaults (can be overridden by Algorithm Adaptor)
    MAX_DAILY_TWEETS: int = 15
    MAX_DAILY_REPLIES: int = 15
    MAX_MONTHLY_POSTS: int = 500
    MAX_MONTHLY_READS: int = 100
    MIN_TWEET_INTERVAL_SECONDS: int = 1800 

    class Config:
        env_file = ".env"
        extra = "ignore" 

# --- Loader ---
def load_accounts(config_path: str) -> List[AccountConfig]:
    if not os.path.exists(config_path):
        return []
    
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
        
    if not data or "accounts" not in data:
        return []
        
    accounts = []
    for acc_data in data["accounts"]:
        try:
            accounts.append(AccountConfig(**acc_data))
        except Exception as e:
            print(f"Error loading account {acc_data.get('id', 'unknown')}: {e}")
            
    return accounts

# Initialize Global Config
config = SystemConfig()

