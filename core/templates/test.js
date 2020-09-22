var AWS = require('aws-sdk');
var Excel = require('exceljs');
var XLSX = require('xlsx');
var Stream = require('stream');

AWS.config.update(
  {
    accessKeyId: "AKIAX6CEC3CGR3ZJ6DHQ",
    secretAccessKey: "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",
  }
);
var s3 = new AWS.S3();
wb = s3.getObject(
  { Bucket: "projectcharon", Key: "static/CT-Template.xlsx" },
  function (error, data) {
    if (error != null) {
    } else {
      var workbook = XLSX.read(data.Body);
      let wb = new Excel.Workbook();

      let stream = new Stream.Readable();
      stream.push(data.Body);
      stream.push(null);
        wb.xlsx.read(stream).then((wb)=> {
          var worksheet = wb.getWorksheet('Data');
          worksheet.getCell('B3').value = "abc";
          return wb.xlsx.writeFile('file.xlsx')
        });
    }
  }
);
console.log(wb);