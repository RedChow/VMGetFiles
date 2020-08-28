<h1>Moving Files From Virtual Machines to Host Machine Automatically with PyQt and Python</h1>
<p>
At home I run a Fedora 31 Workstation, along with several other Linux distros on other machines. But, the Fedora
workstation serves as one of two Plex servers (mainly movies/tv/sports while the other serves photos and family videos) and code development. 
To keep things nice and organized and to keep Plex running smoothly, I have installed several virtual machines.
Sometimes I need to transfer files between the VMs and the host mahcine.
I keep a partition under /tmp/share to share files between the systems.
I'm a bit lazy and don't want to manually upload/download files between the VMs and host machine. So,
I did what any other programmer would do and spent 10 times the amount of time developing a program
than to just manually upload/download the files. However, the few hours I spent one Saturday afternoon
developing this program has already paid off in that I can walk away at any time and the files will 
automatically upload/download. No need to sit and wait for file transfers...no need to double check that I
uploaded everything I should and so on.
</p>
<h2>Basics of the Program</h2>
<p>
The download portion of the program uses PyQt5. Something similar could have been done without PyQt5; it just makes
some things a bit easier. One such item is the QFileSystemWatcher. Also I like using signals/slots architecture.
 QFileSystemWatcher will detect changes in a folder.
Once changes have been detected, you can connect slots to perform work on that change.
</p>

<p>
The class MainWatcher listens to /tmp/share/mysubfolder1, /tmp/share/mysubfolder2, etc and listens for changes to those
folders. 
(On the VMs I keep a somewhat similar folder structure to that of the host machaine. 
This simplifies moving files and subfolders easier. For example, /tmp/share/mysubfolder1 will correspond
to /home/me/mysubfolder1.)
Once a change is detected, we look into that folder to see if a folder or file has been uploaded. 
</p>

<p>
There are two other classes: SubFolderWatcher and FileWatcher. 
If a folder has been uploaded, we create an instance of SubFolderWatcher.
Similarly, if a file has been uploaded we create an instance of FileWatcher.
FileWatcher is a subclass of SubFolderWatcher.
Once an instance of the two has been created, we get all the last modified times of all the folder contents or file.
A timer then starts to check if the modified times of the contents/file has changed.
If no change in the modified time is detected, the folder or file is safe to copy to the host machine.
This will ensure we don't try to download an incomplete folder or file.
(NOTE: On Windows, I think you have to use something other than stat(path).st_mtime. I can't remember off the top of my head
which stat to use.)
Lastly, once a folder or file has been copied, we emit a signal back to MainWatcher to remove the path of the copied folder/file.
</p>

<p>
There are some commented out sections in the copy_folder and copy_file methods. These code blocks run shutil.chown to change permissions 
on the file(s). chmod is also called to change read/write/execute permissions. This is necessary sometimes for the Plex server; files
need certain permissions in order for it to be shown.
</p>
