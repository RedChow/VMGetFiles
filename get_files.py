import sys
import shutil
from os import listdir, stat, remove, chmod, walk
from os.path import isfile, join, exists, normpath, split, basename, isdir
from pathlib import Path
from PyQt5.QtCore import QFileSystemWatcher, pyqtSlot, QObject, QTimer, pyqtSignal
from PyQt5.QtWidgets import QSystemTrayIcon, QApplication


local_paths = ['/tmp/share/myfolder/{0}'.format(ending) for ending in ['list your sub folders here']]
home = '/path/to/home'
timer_delay = 30


class MainWatcher:
    def __init__(self):
        self.watcher = QFileSystemWatcher()
        self.folders = []
        self.files = []

    def connect(self):
        self.watcher.directoryChanged.connect(self.directory_changed)

    def add_paths(self, list_of_paths):
        self.watcher.addPaths(list_of_paths)

    def directory_changed(self, path):
        for f in listdir(path):
            complete_path = join(path, f)
            sub_folder = self.map_path_to_folder_id(path)
            if not exists(complete_path):
                continue
            if complete_path in self.folders or complete_path in self.files:
                continue
            if isfile(complete_path):
                fw = FileWatcher()
                fw.subfolder = sub_folder
                fw.base_path = complete_path
                fw.connect()
                fw.finished.connect(self.copied_file)
                self.files.append(fw)
            else:
                fw = SubFolderWatcher()
                fw.base_path = complete_path
                fw.subfolder = sub_folder
                fw.connect()
                fw.finished.connect(self.copied_folder)
                self.folders.append(fw)

    def copied_file(self, path):
        try:
            i = self.files.index(path)
        except IndexError:
            pass
        else:
            del self.files[i]

    def copied_folder(self, path):
        try:
            i = self.folders.index(path)
        except IndexError:
            pass
        else:
            del self.folders[i]

    @staticmethod
    def map_path_to_folder_id(path):
        normalized_path = normpath(path)
        ending = split(normalized_path)[-1]
        return ending


class SubFolderWatcher(QObject):
    finished = pyqtSignal(str, int)

    def __init__(self):
        super(SubFolderWatcher, self).__init__()
        self.base_path = ''
        self.subfolder = ''
        self.files = {}
        self.finished_checking = False
        self.watcher = QFileSystemWatcher()
        self.timer = QTimer()
        self.check_threshold = 3
        self.check_number = 0
        self.sub_folder = ''

    def connect(self):
        self.watcher.addPaths([self.base_path])
        self.watcher.directoryChanged.connect(lambda y: self.directory_changed(y))
        self.watcher.fileChanged.connect(lambda x: self.file_changed(x))
        self.timer.timeout.connect(self.check_files)
        self.timer.start(timer_delay*1000)

    def check_files(self):
        finished = True
        if exists(self.base_path):
            for sub_path in Path(self.base_path).rglob('*'):
                new_st_mtime = int(stat(sub_path).st_mtime)
                path_name = normpath(sub_path)
                if path_name not in self.files:
                    self.files[path_name] = new_st_mtime
                if self.files[path_name] != new_st_mtime:
                    finished = False
                self.files[path_name] = new_st_mtime
            if finished:
                self.check_number += 1
            if self.check_number > self.check_threshold:
                self.timer.stop()
                self.watcher.removePath(self.base_path)
                self.copy_folder()
        else:
            self.finished_checking = True

    def copy_file(self):
        pass

    def copy_folder(self):
        try:
            shutil.move(self.base_path, join(home, self.subfolder))
        except shutil.Error:
            remove(self.base_path)
        else:
            pass
            """
            NOTE:
            On my home system, I sometimes use the following code to change groups and owner permissions of the
            copied files. 
            I would personally not use this in a production environment, especially with the 775 permissions. 
            The following code doesn't make sense to run on Windows, so you can ignore if you're on that system.
            
            local = join(home, self.subfolder)
            chmod(local, 0o775)
            shutil.chown(local, 'grp', 'usr')
            for root, dirs, files in walk(local):
                chmod(root, 0o775)
                shutil.chown(root, 'grp', 'usr')
                for file_name in files:
                    chmod(join(root, file_name), 0o775)
                    shutil.chown(join(root, file_name), 'grp', 'usr')
            """
        self.finished_checking = True
        self.finished.emit(self.base_path)

    @pyqtSlot(str)
    def directory_changed(self, path):
        if self.timer.isActive():
            self.timer.stop()
            self.timer.start(timer_delay*1000)
        for sub_path in Path(path).rglob('*'):
            if isfile(sub_path):
                path_name = normpath(join(path, sub_path.name))
                self.files[path_name] = int(stat(self.base_path).st_mtime)

    def file_changed(self):
        pass

    def __eq__(self, other):
        try:
            return other.base_path == self.base_path
        except AttributeError:
            return other == self.base_path


class FileWatcher(SubFolderWatcher):
    finished = pyqtSignal(str, int)

    def __init__(self):
        super(FileWatcher, self).__init__()
        self.st_mtime = 0

    @pyqtSlot(str)
    def directory_changed(self, null_path):
        pass

    @pyqtSlot(str)
    def file_changed(self, null_path):
        if self.timer.isActive():
            self.timer.stop()
            self.timer.start(timer_delay*1000)

    def check_files(self):
        if exists(self.base_path):
            new_st_mtime = int(stat(self.base_path).st_mtime)
            if self.st_mtime == new_st_mtime:
                self.timer.stop()
                self.watcher.removePath(self.base_path)
                self.copy_file()
            self.st_mtime = new_st_mtime
        else:
            self.finished_checking = True

    def copy_file(self):
        try:
            shutil.move(self.base_path, join(home, self.subfolder))
        except shutil.Error:
            remove(self.base_path)
        else:
            base_path_parts = split(self.base_path)
            new_path = join(home, self.subfolder, base_path_parts[-1])
            """
            NOTE: On my home system I use this to change permissions on the copied files.
            
            shutil.chown(new_path, 'usr', 'grp')
            chmod(join(home, self.subfolder), 0o755)
            """
        self.finished_checking = True
        self.finished.emit(self.base_path)


if __name__ == '__main__':
    a = QApplication(sys.argv)
    main_watcher = MainWatcher()
    main_watcher.add_paths(local_paths)
    main_watcher.connect()
    sys.exit(a.exec_())
