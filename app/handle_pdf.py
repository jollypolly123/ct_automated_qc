from PyPDF2 import PdfFileReader, PdfFileWriter
import io
import boto3
from datetime import date
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


def get_template():
    s3 = boto3.client('s3', aws_access_key_id="AKIAX6CEC3CGR3ZJ6DHQ",
                      aws_secret_access_key="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")
    bucket_object = s3.get_object(Bucket='projectcharon', Key='static/CTQCForm.pdf')
    existing_pdf = PdfFileReader(io.BytesIO(bucket_object['Body'].read()))
    return existing_pdf


def combine_pdfs(existing_pdf, new_pdf):
    output = PdfFileWriter()
    page = existing_pdf.getPage(0)
    page.mergePage(new_pdf.getPage(0))
    output.addPage(page)
    temp_pdf = io.BytesIO()
    output.write(temp_pdf)

    name = 'CT_QC_' + date.today().strftime("%m_%d_%Y") + '.pdf'

    s3 = boto3.client('s3', aws_access_key_id="AKIAX6CEC3CGR3ZJ6DHQ",
                      aws_secret_access_key="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")
    s3.put_object(Body=temp_pdf.getvalue(), Bucket='projectcharon', Key=name)


if __name__ == '__main__':
    get_template()
    # packet = io.BytesIO()
    # can = canvas.Canvas(packet, pagesize=letter)
    # can.setFillColorRGB(0.2, 0.5, 0.3)
    # can.drawString(120, 670, "bing")
    # can.drawString(120, 652, "bloop")
    # can.drawString(120, 635, "bksdj")
    # can.drawString(120, 618, "bonky")
    # can.drawString(120, 600, "bonky")
    # can.drawString(120, 582, "bonky")
    # can.drawString(120, 564, "bonky")
    # can.drawString(120, 546, "bonky")
    # can.drawString(120, 528, "bonky")
    # can.drawString(120, 510, "bonky")
    # can.drawString(120, 494, "bonky")
    # can.drawString(120, 476, "bonky")
    # can.drawString(120, 458, "bonky")
    # can.drawString(120, 440, "bonky")
    # can.drawString(120, 423, "bonky")
    # can.drawString(120, 406, "bonky")
    # can.drawString(120, 388, "bonky")
    # can.drawString(120, 370, "bonky")
    # can.drawString(120, 352, "bonky")
    # can.drawString(120, 334, "bonky")
    # can.drawString(120, 316, "bonky")
    # can.drawString(120, 297, "bonky")
    # can.drawString(120, 280, "bonky")
    # can.drawString(120, 262, "bonky")
    # can.drawString(120, 245, "bonky")
    # can.drawString(120, 228, "bonky")
    # can.drawString(120, 210, "bonky")
    # can.drawString(120, 192, "bonky")
    # can.drawString(120, 174, "bonky")
    # can.drawString(120, 156, "bonky")
    # can.drawString(120, 138, "bonky")
    #
    # can.drawString(177, 670, "bonky")
    # can.drawString(177, 652, "bloop")
    # can.drawString(177, 635, "bksdj")
    # can.drawString(177, 618, "bonky")
    # can.drawString(177, 600, "bonky")
    # can.drawString(177, 582, "bonky")
    # can.drawString(177, 564, "bonky")
    # can.drawString(177, 546, "bonky")
    # can.drawString(177, 528, "bonky")
    # can.drawString(177, 510, "bonky")
    # can.drawString(177, 494, "bonky")
    # can.drawString(177, 476, "bonky")
    # can.drawString(177, 458, "bonky")
    # can.drawString(177, 440, "bonky")
    # can.drawString(177, 423, "bonky")
    # can.drawString(177, 406, "bonky")
    # can.drawString(177, 388, "bonky")
    # can.drawString(177, 370, "bonky")
    # can.drawString(177, 352, "bonky")
    # can.drawString(177, 334, "bonky")
    # can.drawString(177, 316, "bonky")
    # can.drawString(177, 297, "bonky")
    # can.drawString(177, 280, "bonky")
    # can.drawString(177, 262, "bonky")
    # can.drawString(177, 245, "bonky")
    # can.drawString(177, 228, "bonky")
    # can.drawString(177, 210, "bonky")
    # can.drawString(177, 192, "bonky")
    # can.drawString(177, 174, "bonky")
    # can.drawString(177, 156, "bonky")
    # can.drawString(177, 138, "bonky")
    #
    # can.drawString(225, 670, "bonky")
    # can.drawString(225, 652, "bloop")
    # can.drawString(225, 635, "bksdj")
    # can.drawString(225, 618, "bonky")
    # can.drawString(225, 600, "bonky")
    # can.drawString(225, 582, "bonky")
    # can.drawString(225, 564, "bonky")
    # can.drawString(225, 546, "bonky")
    # can.drawString(225, 528, "bonky")
    # can.drawString(225, 510, "bonky")
    # can.drawString(225, 494, "bonky")
    # can.drawString(225, 476, "bonky")
    # can.drawString(225, 458, "bonky")
    # can.drawString(225, 440, "bonky")
    # can.drawString(225, 423, "bonky")
    # can.drawString(225, 406, "bonky")
    # can.drawString(225, 388, "bonky")
    # can.drawString(225, 370, "bonky")
    # can.drawString(225, 352, "bonky")
    # can.drawString(225, 334, "bonky")
    # can.drawString(225, 316, "bonky")
    # can.drawString(225, 297, "bonky")
    # can.drawString(225, 280, "bonky")
    # can.drawString(225, 262, "bonky")
    # can.drawString(225, 245, "bonky")
    # can.drawString(225, 228, "bonky")
    # can.drawString(225, 210, "bonky")
    # can.drawString(225, 192, "bonky")
    # can.drawString(225, 174, "bonky")
    # can.drawString(225, 156, "bonky")
    # can.drawString(225, 138, "bonky")
    #
    # can.drawString(270, 670, "P")
    # # x=120, 177, 225, 272
    # # y=670 for row 1
    # # 17.5 pixel increment by row
    # can.save()
    # packet.seek(0)
    # new_pdf = PdfFileReader(packet)
    #
    # existing = get_template()
    # combine_pdfs(existing, new_pdf)
