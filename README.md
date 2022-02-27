
To use it, first find `# Create authentication` code segment in `autoliker.py` and fill it out with your data:
```
  # Create authentication:
        self.auth_id = "your user auth ID"
        self.cookies = "put your cookies here...fp=; sess=; csrf=; ref_src=; auth_id=; st=;"
        self.user_agent = "Mozilla/5.0...this is your user agent"
        self.app_token = "whatever app token is at the moment"
        self.x_bc ="your x-bc"
```

To run it, specify OF username as an argument. 
Example: `python autoliker.py belledelphine`.

Tested with python 3.9