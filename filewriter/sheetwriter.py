from filewriter.helper import writesheet, addtimemeasurements, averagetriplicates
from framework.abstract.abstract_workbook import  AbstractWorkbook


################### UNFINISHED ########################


# class WriteSheet(AbstractWorkbook):
#     def __init__(
#             self,
#             sheet:  = None,
#             processed_data: [] = None ):
#         self.original = original_data
#         self.processed = processed_data
#
# class ImportValidator(AbstractValidator):
#     repository = None
#
#     def __init__(self):
#         self.repository = Repository()
#
#     def execute(self, request) -> Response:
#         if request.files['file'] is None:
#             return Response(False, 'File is required')