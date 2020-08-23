Name: Zaid Naji
Infra provisioning assessment (Ec2 deployment)

- Deployment for infra is done through boto3 (as Cloudformation/terraform/IaaC were not allowed in the requirements)
- Requires atleast Python 3.6
- Install dependencies
```bash
pip install -r requirements.txt
```
- To run the demo
```bash
python ./createWebInfra.py
```

- To tear down the infra
```bash
python ./createWebInfra.py --teardown
```

