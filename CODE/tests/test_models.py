from client.models import FileItem, FileStatus

item = FileItem(path="uploads/document.pdf")

print("Tên file:", item.name)
print("Trạng thái:", item.status.value)
print("Tiến độ:", item.progress)

item.status = FileStatus.SENDING
item.progress = 50
print("Trạng thái mới:", item.status.value)
print("Tiến độ mới:", item.progress)

item.status = FileStatus.COMPLETED
item.progress = 100
print("Trạng thái cuối:", item.status.value)
print("Tiến độ cuối:", item.progress)

item.status = FileStatus.ERROR
item.error_message = "Không thể gửi file"
print("Trạng thái lỗi:", item.status.value)
print("Thông báo:", item.error_message)