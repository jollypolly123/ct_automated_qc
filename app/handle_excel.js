var Excel = require('exceljs');
var workbook = new Excel.Workbook();
workbook.xlsx.readFile('file.xlsx')//Change file name here or give file path
.then(function() {
    var worksheet = workbook.getWorksheet('sheet');
    var i=1;
    worksheet.eachRow({ includeEmpty: false }, function(row, rowNumber) {
      r=worksheet.getRow(i).values;
      r1=r[2];// Indexing a column
      console.log(r1);
      i++;
    });
    worksheet.getCell('B3').value = "abc";//Change the cell number here
return workbook.xlsx.writeFile('file.xlsx')//Change file name here or give     file path
   });