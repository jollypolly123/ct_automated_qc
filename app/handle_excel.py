import openpyxl
import cloudconvert
import boto3
import io


def get_template():
    s3 = boto3.client('s3', aws_access_key_id="AKIAX6CEC3CGR3ZJ6DHQ",
                      aws_secret_access_key="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")
    bucket_object = s3.get_object(Bucket='projectcharon', Key='static/CT-Report.xlsx')
    content = bucket_object['Body'].read()
    wb = openpyxl.load_workbook(io.BytesIO(content))
    return wb


def publish_cc_wb(key):
    cloudconvert.configure(api_key=key, sandbox=False)
    cloudconvert.Job.create(payload={
        "tasks": {
            'import-my-file': {
                'operation': 'import/url',
                'url': 'https://projectcharon.s3.amazonaws.com/static/CT-Report.xlsx',
            },
            'convert-my-file': {
                'operation': 'convert',
                'input': 'import-my-file',
                "input_format": "xlsx",
                'output_format': 'pdf',
                "page_range": "1-2",
                "optimize_print": True
            },
            'export-my-file': {
                'operation': 'export/s3',
                'input': 'convert-my-file',
                "access_key_id": "AKIAX6CEC3CGR3ZJ6DHQ",
                "secret_access_key": "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",
                'region': 'us-east-1',
                "bucket": "projectcharon",
            }
        },
        "tag": "myjob-123"
    })


if __name__ == "__main__":
    # cc_api_key = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiNGU3NGEyYzU5OTkxZmRmOWE0OTY2NjNhOGVhZ" \
    #              "jFiOGE1YzBlMWQzOGUzMzhhYzBjYTJmZmFkMTdhNjJhNjg0ZThiOWM0MzY2ZWQ5YmU0YzciLCJpYXQiOjE2MDAxNDc0ODMsIm5" \
    #              "iZiI6MTYwMDE0NzQ4MywiZXhwIjo0NzU1ODIxMDgzLCJzdWIiOiI0NDk5ODk2MCIsInNjb3BlcyI6WyJ1c2VyLnJlYWQiLCJ1c" \
    #              "2VyLndyaXRlIiwidGFzay5yZWFkIiwid2ViaG9vay5yZWFkIiwidGFzay53cml0ZSIsIndlYmhvb2sud3JpdGUiLCJwcmVzZXQ" \
    #              "ucmVhZCIsInByZXNldC53cml0ZSJdfQ.qOuoZmrynlRPhf60cbJbPccDTlOfc2OQMh6FyslSdWfkov9Ppp7HvSX_mTaiB8k9qF" \
    #              "0SKsfOxNBQ5_eh4oaLLYlgo71w4nNj_mGv0C3ymIVRMq6oTcoKPYEVYmBk4Pxitpwm7DgPsLRP6hOhtZJlIjb1S12hLE1N8vnn" \
    #              "oRkY2WsZE9bd6l2qVjnhHWk2se54SkbD-J7E_3OGx543Tfrgq8UxQerR1BOAkSu9C6zXGxrjv1mCYEy70k9BgSeS-QkEuUvt3I" \
    #              "uEGdBYYEdbXf826WQSrKO7T3QK_1YN93Bkqa0nPmug6qdbSBalYhOc5l-HfDdU9M1-kojE6RNy4C5M8Vid6LY9Zf7wImxeCG1P" \
    #              "uL-Adtww112uTlvl8Vi7cNMrCZ1sWg-Q0i3iabjJqxvRfhjDhJj2beI3cictvFryLLhWm6VQoVFHDFuLhUHSOppoLOFxMR6Mew" \
    #              "9vN3YDjpkCzBBThzHdKTL6qImPozcAgwzxbSvpIIyJKY_p6UPQYPkaVxo5Hcgx805OODv-NiJ2q4ublO-RDcKH1p2Znvil1hbw" \
    #              "NOQ15nKH5jFDf2HqT-54psaxaz3oTzHtu8LL79wKc99PAl78Gi-FjQWb5AXrHurhGroJTaZFQygl7Gb7KTnLJ9Wl8NEzo_QyDJ" \
    #              "-EsNq_rOZwLrf3Pb6Ffi4BeseKEFM"
    # publish_cc_wb(cc_api_key)
    work = get_template()
    print(work['Summary']['A1'])
