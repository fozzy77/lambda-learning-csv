# lambda-learning-csv
This is a fundamental test with lambda and s3 interaction

I have been trying to learn Lambda with some functional interaction to s3.

vpc_size = messageData['body'] driven from an event such as SQS. Derives the vpc constructs from data in the body as a single string
like;
small, medium or large.

This is a work in progress project. 

3 Files are held in S3 
example-large.csv
example-medium.csv
example-small.csv

Row 2 contains an array of available CIDR spaces 
x.x.x.x/22 within the large csv
x.x.x.x/23 within the medium csv
x.x.x.x/24 within the small csv 

The main objective is a simple idea of obtaining IP data, albeit I havent tested the reverse .

It uses basic iteration to read from a list, then remove the entry so on next read is the next on the list etc.

You need to update the lambda variables with unique_bucket with the S3 bucket name you have, and also allow lambda the;

execution permissions for sqs interaction and s3

AWSLambdaSQSQueueExecutionRole
AmazonS3ObjectLambdaExecutionRolePolicy

Also note endpoints are created here so ensure you destroy if not required the default is omitted
