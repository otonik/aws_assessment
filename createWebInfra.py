import os
import sys

import boto3
import time
from botocore.exceptions import ClientError
from string import Template


class CreateWebInfra:
    def __init__(self):
        self.ec2_client = boto3.client("ec2")
        self.ec2_resource = boto3.resource("ec2")
        self.AMI_ID = "ami-0d8f6eb4f641ef691"
        self.INSTANCE_TYPE = "t2.micro"
        self.TAG_SPEC = [
            {
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "hello-world-service", "Value": "hello-world-service",},
                ],
            },
        ]

    def tear_down_resources(self):
        custom_filter = [
            {"Name": "tag:hello-world-service", "Values": ["hello-world-service"]}
        ]
        print("tearing down infrastructure...")
        instances = []
        try:
            response = self.ec2_client.describe_instances(Filters=custom_filter)
            for r in response["Reservations"]:
                for i in r["Instances"]:
                    # FIXME: check if instance is not running
                    instances.append(i["InstanceId"])
                    print("terminating instance:%s" % i["InstanceId"])

            waiter = self.ec2_client.get_waiter("instance_terminated")

            if len(instances) > 0:
                self.ec2_client.terminate_instances(InstanceIds=instances)
                waiter.wait(InstanceIds=instances)

            response = self.ec2_client.describe_security_groups(Filters=custom_filter)
            for r in response["SecurityGroups"]:
                print("deleting security group:%s" % r["GroupId"])
                self.ec2_client.delete_security_group(GroupId=r["GroupId"])

            response = self.ec2_client.describe_key_pairs(Filters=custom_filter)
            for r in response["KeyPairs"]:
                self.ec2_client.delete_key_pair(KeyPairId=r["KeyPairId"])

        except ClientError as e:
            print(e)

    def create_key_pair(self):

        self.TAG_SPEC[0]["ResourceType"] = "key-pair"
        response = self.ec2_resource.create_key_pair(
            KeyName="ec2-keypair", TagSpecifications=self.TAG_SPEC
        )
        KeyPairOut = str(response.key_material)

        with open("ec2-keypair.pem", "w") as keypair_file:
            keypair_file.write(KeyPairOut)

        return response

    def create_web_app_ec2(self, security_group_id: str):

        self.TAG_SPEC[0]["ResourceType"] = "instance"
        # read user data script
        print("creating backend instances...")
        with open("./files/node_deploy.sh", "r") as userdata:
            instance = self.ec2_resource.create_instances(
                ImageId=self.AMI_ID,
                InstanceType=self.INSTANCE_TYPE,
                MinCount=1,
                MaxCount=2,
                KeyName="ec2-keypair",
                SecurityGroupIds=[security_group_id],
                TagSpecifications=self.TAG_SPEC,
                UserData=userdata.read(),
            )
        print("created instances %s" % instance)

        return instance

    def create_nginx_ec2(self, security_group_id: str, private_ips: list):

        self.TAG_SPEC[0]["ResourceType"] = "instance"
        try:
                
            backend_servers = {}
            for i, val in enumerate(private_ips):
                backend_servers["backend_server" + str(i)] = val

            # TODO: make template more dynamic
            with open("./files/nginx_deploy.sh", "r") as userdata:
                src = Template(userdata.read())
                userdata_template = src.substitute(backend_servers)
                print(userdata_template)
                instance = self.ec2_resource.create_instances(
                    ImageId=self.AMI_ID,
                    InstanceType=self.INSTANCE_TYPE,
                    MinCount=1,
                    MaxCount=1,
                    KeyName="ec2-keypair",
                    SecurityGroupIds=[security_group_id],
                    TagSpecifications=self.TAG_SPEC,
                    UserData=userdata_template,
                )

                return instance
        except Exception(e):
            print(e)

    def create_security_group(self):

        self.TAG_SPEC[0]["ResourceType"] = "security-group"

        try:

            print("creating new security group...")
            response = self.ec2_client.describe_vpcs()
            vpc_id = response.get("Vpcs", [{}])[0].get("VpcId", "")

            response = self.ec2_client.create_security_group(
                GroupName="hello-world-sg",
                Description="demo-sg",
                VpcId=vpc_id,
                TagSpecifications=self.TAG_SPEC,
            )
            security_group_id = response["GroupId"]
            print("security group created %s in vpc %s." % (security_group_id, vpc_id))

            self.ec2_client.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[
                    {
                        "IpProtocol": "tcp",
                        "FromPort": 80,
                        "ToPort": 80,
                        "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                    },
                    {
                        "IpProtocol": "tcp",
                        "FromPort": 22,
                        "ToPort": 22,
                        "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                    },
                    {
                        "IpProtocol": "-1",
                        "FromPort": -1,
                        "ToPort": -1,
                        "UserIdGroupPairs": [{"GroupId": security_group_id}],
                    },
                ],
            )
            print("added inbound rules for security group:%s" % security_group_id)
            return security_group_id

        except ClientError as e:
            print(e)

    def deploy(self):
        try:
            print("starting new infra...")
            self.create_key_pair()
            sg_id = self.create_security_group()
            response = self.create_web_app_ec2(sg_id)

            instances = response
            private_ips = [instance.private_ip_address for instance in instances]
            map(lambda x: x.wait_until_exists(), instances)

            response = self.create_nginx_ec2(sg_id, private_ips)
            instances.extend(response[0])

            map(lambda x: x.wait_until_running(), instances)
            print("waiting for all instances to run...")

            # print(response)

        except Exception as e:
            print(e)


if __name__ == "__main__":
    # assumes existing VPC and IAM role with enough privileges
    if len(sys.argv) > 1 and sys.argv[1] == "--teardown":
        CreateWebInfra().tear_down_resources()
    else:
        CreateWebInfra().deploy()
