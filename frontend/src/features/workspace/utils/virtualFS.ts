import { FileItem } from '../../../state';

export interface FileSystemNode {
  name: string;
  path: string; // absolute OS path for files, virtual slash-separated path for directories
  is_directory: boolean;
  size?: number;
  modified?: string;
  type?: string;
}

/**
 * Computes virtual directories and files directly under a given currentDirectory path
 * based on recursive absolute file paths returned from the backend.
 */
export const getVirtualNodes = (files: FileItem[], currentDir: string): FileSystemNode[] => {
  const nodesMap = new Map<string, FileSystemNode>();
  
  // Normalize directories to forward slashes
  const canonicalCurrentDir = currentDir === '/' ? '/' : currentDir.replace(/\\/g, '/');

  files.forEach((file) => {
    // Normalize path to forward slashes
    const normalizedFilePath = file.path.replace(/\\/g, '/');

    // Identify where standard directories like Desktop, Documents, Downloads sit in the path
    const match = normalizedFilePath.match(/\/(Desktop|Documents|Downloads)(\/.*)?$/i);
    
    if (!match) {
      // Fallback: File is not under Desktop/Documents/Downloads. Put it in root "/"
      if (canonicalCurrentDir === '/') {
        const parts = normalizedFilePath.split('/');
        const name = parts[parts.length - 1] || file.name;
        nodesMap.set(file.path, {
          name,
          path: file.path,
          is_directory: false,
          size: file.size,
          modified: file.modified,
          type: file.type
        });
      }
      return;
    }

    const rootDirName = match[1]; // "Desktop", "Documents", "Downloads"
    const subPath = match[2] || ''; // e.g. "/Folder/file.txt" or "/file.txt" or empty

    // Construct the virtual directory hierarchy
    // Virtual folder path will look like "/Documents" or "/Documents/Folder"
    const subParts = subPath.split('/').filter(Boolean); // e.g. ["Folder", "file.txt"]
    
    // File is directly in virtual root matching folder
    if (subParts.length === 0) {
      // It is a directory node in root "/"
      if (canonicalCurrentDir === '/') {
        nodesMap.set('/' + rootDirName, {
          name: rootDirName,
          path: '/' + rootDirName,
          is_directory: true
        });
      }
      return;
    }

    // Determine target virtual directory and filename
    const virtualParentParts = ['/' + rootDirName, ...subParts.slice(0, subParts.length - 1)];
    const virtualFolder = virtualParentParts.join('/').replace(/\/+/g, '/');
    const virtualFileName = subParts[subParts.length - 1];

    if (virtualFolder === canonicalCurrentDir) {
      // The file is directly inside the current directory
      nodesMap.set(file.path, {
        name: virtualFileName,
        path: file.path,
        is_directory: false,
        size: file.size,
        modified: file.modified,
        type: file.type || virtualFileName.split('.').pop()
      });
    } else if (virtualFolder.startsWith(canonicalCurrentDir === '/' ? '/' : canonicalCurrentDir + '/')) {
      // The file is in a deeper subfolder. We should render the immediate child folder node
      // under canonicalCurrentDir
      const relativePath = virtualFolder.substring(canonicalCurrentDir === '/' ? 1 : canonicalCurrentDir.length + 1);
      const immediateSubFolderName = relativePath.split('/')[0];
      const immediateSubFolderPath = (canonicalCurrentDir === '/' ? '/' : canonicalCurrentDir + '/') + immediateSubFolderName;

      nodesMap.set(immediateSubFolderPath, {
        name: immediateSubFolderName,
        path: immediateSubFolderPath,
        is_directory: true
      });
    }
  });

  // Make sure default folders Desktop, Documents, Downloads exist in "/"
  if (canonicalCurrentDir === '/') {
    ['Desktop', 'Documents', 'Downloads'].forEach((folder) => {
      const virtualPath = '/' + folder;
      if (!nodesMap.has(virtualPath)) {
        nodesMap.set(virtualPath, {
          name: folder,
          path: virtualPath,
          is_directory: true
        });
      }
    });
  }

  return Array.from(nodesMap.values());
};
