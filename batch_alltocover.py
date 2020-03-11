# -*- coding: UTF-8 -*-
import os
import os.path

# 定义文件类
class File(object):
	def __init__(self, name, path):
		# 文件名
		self.name = name
		# 文件路径
		self.path = path
	
	# 获取文件的全路径
	def getFullPath(self):
		return os.path.join(self.path, self.name)

def changeImageName():
	for parent, dirs, files in os.walk("G:\\spider\\workall\\ontto\\bash_tocover"):
		# 遍历所有文件，将其存为文件类型并封装到集合中返回
		for fileName in files:
			sourcefile = File(fileName, parent)
			coverdir = fileName[0:(len(fileName)-4)]
			newImgUrl = "G:\\spider\\workall\\ontto\\tocover" + "\\" + coverdir
			if not os.path.exists(newImgUrl):
				os.mkdir(newImgUrl)
			newImgPath = newImgUrl + "\\cover.jpg"
			file(newImgPath, "w").truncate()
			open(newImgPath, "wb").write(open(sourcefile.getFullPath(), "rb").read())
			print(newImgPath)

if __name__ == "__main__":
	changeImageName()