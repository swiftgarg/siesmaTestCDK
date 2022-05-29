from aws_cdk import (aws_ecs as ecs, aws_ecr as ecr, aws_ec2 as ec2, aws_iam as iam, aws_ecs_patterns as ecs_patterns, Stack, CfnOutput)
from constructs import Construct

class siesmaECSCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create the ECR Repository
        ecr_repository = ecr.Repository(self,
                                        "ecs-siesma-repository",
                                        repository_name="ecs-siesma-repository")

        # Create the ECS Cluster (and VPC)
        # Deploying to only two AZ to save money
        vpc = ec2.Vpc(self,
                      "ecs-siesma-vpc",
                      max_azs=2)
        cluster = ecs.Cluster(self,
                              "ecs-siesma-cluster",
                              cluster_name="ecs-siesma-cluster",
                              vpc=vpc)

        # Create the ECS Task Definition with placeholder container (and named Task Execution IAM Role)
        execution_role = iam.Role(self,
                                  "ecs-siesma-execution-role",
                                  assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
                                  role_name="ecs-siesma-execution-role")
        execution_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            resources=["*"],
            actions=[
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
                ]
        ))
        task_definition = ecs.FargateTaskDefinition(self,
                                                    "ecs-siesma-task-definition",
                                                    execution_role=execution_role,
                                                    family="ecs-siesma-task-definition")
        container = task_definition.add_container(
            "ecs-siesma",
            image=ecs.ContainerImage.from_registry("amazon/amazon-ecs-sample"),
        )
        container.add_port_mappings(ecs.PortMapping(container_port=8080, host_port=8080, protocol=ecs.Protocol.TCP))

        # Create the ECS Service, NLB backed for access
        ## We set very low cap and desired capacity. We can also
        ## setup an autoscaling group here which scales up our
        ## instances based on our cpu / memory / traffic
        fargate_service = ecs_patterns.NetworkLoadBalancedFargateService(
            self, "ecs-siesma-service",
            cluster = cluster,
            task_definition = task_definition,
            service_name = "ecs-siesma-service",
            listener_port=8080,
            cpu=256,
            memory_limit_mib=512,
            desired_count=1
        )

        fargate_service.service.connections.security_groups[0].add_ingress_rule(
            peer = ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection = ec2.Port.tcp(8080),
            description="Allow http inbound from VPC"
        )

        CfnOutput(
            self, "LoadBalancerDNS",
            value=fargate_service.load_balancer.load_balancer_dns_name
        )