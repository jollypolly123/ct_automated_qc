import execjs

ctx = execjs.compile('''
function aFunction() {
    console.log("hi");
    var AWS = require('aws-sdk');
    var Excel = require('exceljs');
    var XLSX = require('xlsx');
    var s3 = new AWS.S3();
    AWS.config.update(
      {accessKeyId: "AKIAX6CEC3CGR3ZJ6DHQ",
       secretAccessKey: "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"}
    );
    wb = s3.getObject(
      { Bucket: "projectcharon", Key: "static/CT-Template.xlsx" },
      function (error, data) {
        if (error != null) {
        } else {
          var workbook = XLSX.read(data.Body);
          // console.log(data.Body);
          console.log(workbook);
        }
      }
    );
    console.log(wb);
}
''')

wb = ctx.call("aFunction")
print(wb)
