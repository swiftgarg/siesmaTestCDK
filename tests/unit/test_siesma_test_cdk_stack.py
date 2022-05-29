import aws_cdk as core
import aws_cdk.assertions as assertions

from siesma_test_cdk.siesma_test_cdk_stack import SiesmaTestCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in siesma_test_cdk/siesma_test_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SiesmaTestCdkStack(app, "siesma-test-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
