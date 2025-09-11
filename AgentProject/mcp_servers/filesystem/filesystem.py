import os
import shutil
from typing import Any, Dict
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from datetime import datetime
import json

def format_path(status: str, message: str, data: Dict[str, Any] = None, path: str= None) -> str:
    response = {
        'status': status,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }

    if data:
        response.update({'data': data})
    if path:
        response.update({'path': str(Path(path).expanduser().absolute())})

    return json.dumps(response)

mcp = FastMCP('file_system')

@mcp.tool()
async def list_directory_contents(directory_path: str) -> str:
    """List all files and subdirectories in the specified directory.
    
    Args:
        directory_path (str): Path of the directory to list contents from.
                            Supports ~ for home directory and relative paths.
                            
    Returns:
        JSON response with:
        - status: 'success' or 'error'
        - message: Operation result description
        - path: Absolute path of listed directory
        - data: {
            "contents": List of items with type and size info
          }"""
    try:
        path = Path(directory_path).expanduser().absolute()
        if not path.exists():
            return format_path(status='error', message=f'Error: Directory "{directory_path}" does not exist', path=directory_path)
        if not path.is_dir():
            return format_path(status='error',  message=f'Error: "{directory_path}" is not a directory', path=directory_path)

        contents = []
        for item in path.iterdir():
            if item.is_dir():
                contents.append(f'[Directory] {item.name}')
            else:
                contents.append(f'[File] {item.name} (Size: {item.stat().st_size})')
        return format_path(status='success', message=f'Contents of directory "{directory_path}" listed successfully', path=directory_path, data={'contents': contents})
    except Exception as e:
        return format_path(status='error', message=f'Error: {str(e)}', path=directory_path)

@mcp.tool()
async def create_text_file(file_path: str, content: str = '') -> str:
    """Create a text file in the directory
    Args: 
        file_path (str): Path of the file to create. Supports ~ for home directory and relative paths.
        content (str): Initial content to write into the file. Defaults to an empty string.

    Returns:
        JSON response with:
        - status: 'success' or 'error'
        - message: Operation result description
        - path: Absolute path of the created file
        - data: {
            'created': True if file was created, False otherwise,
          }
    """
    try:
        path = Path(file_path).expanduser().absolute()

        if not path.parent.exists():
            return format_path(status='error', message=f'Error: Parent directory of "{file_path}" does not exist', path=file_path)
            
        if path.exists():
            return format_path(status='error', message=f'Error: file "{file_path}" already exists', path=file_path)
        path.write_text(content, encoding='utf-8')
        return format_path(status='success', message=f'Successfully created file "{file_path}"', path=file_path, data={'created': True, 'path': str(path)})
    except Exception as e:
        return format_path(status='error', message=f'Error: {str(e)}', path=file_path)
    
@mcp.tool()
async def read_file(file_path: str) -> str:
    """Read the content of a text file.

    Args:
        file_path (str): Path of the file to read. Supports ~ for home directory and relative paths.

    Returns:
        JSON response with:
        - status: 'success' or 'error'
        - message: Operation result description
         - path: Absolute path of file in the directory
        - data: {
            'content': Content of the file as a string,
            'path': Absolute path of the file
          }
    """
    try: 
        path = Path(file_path).expanduser().absolute()
        if not path.exists():
            return format_path(status='error', message=f'Error: file "{file_path}" does not exist', path=file_path)
        if not path.is_file():
            return format_path(status='error', message=f'Error: file "{file_path}" is not a file', path=file_path)
        return format_path(status='success', message=f'Successfully read file "{file_path}"', path=file_path, data={'content': path.read_text(encoding='utf-8'), 'path': str(path)})
    except Exception as e:
        return format_path(status='error', message=f'Error: {str(e)}', path=file_path)

@mcp.tool()
async def create_directory(directory_path: str) -> str:
    """Create a new directory.

    Args:
        directory_path (str): Path of the directory to create. Supports ~ for home directory and relative paths.

    Returns:
        JSON response with:
        - status: 'success' or 'error'
        - message: Operation result description
         - path: Absolute path of the created directory
        - data: {
            'created': True if directory was created, False otherwise,
            'path': Absolute path of the created directory
          }
    """
    try:
        path = Path(directory_path).expanduser().absolute()
        
        if path.exists():
            return format_path(status='error', message=f'Error: Directory "{directory_path}" already exists', path=directory_path)
            
        path.mkdir(parents=True, exist_ok=False)
        return format_path(status='success', message=f'Successfully created directory "{directory_path}"', path=directory_path, data={'created': True, 'path': str(path)})
    except Exception as e:
        return format_path(status='error', message=f'Error: {str(e)}', path=directory_path)

@mcp.tool()
async def rename_file_or_directory(old_path: str, new_path: str) -> str:
    """Rename or move a file or directory.

    Args:
        old_path (str): Current path of the file or directory to rename/move. Supports ~ for home directory and relative paths.
        new_path (str): New path for the file or directory. Supports ~ for home directory and relative paths.

    Returns:
        JSON response with:
        - status: 'success' or 'error'
        - message: Operation result description
         - path: Absolute path of old file or directory
        - data: {
            'new_path': Absolute path of the renamed/moved file or directory
          }
    """
    try:
        old_path_obj = Path(old_path).expanduser().absolute()
        new_path_obj = Path(new_path).expanduser().absolute()
        if not old_path_obj.exists():
            return format_path(status='error', message=f'Error: "{old_path}" does not exist', path=old_path)
        if new_path_obj.exists():
            return format_path(status='error', message=f'Error: "{new_path}" already exist', path=new_path)
        
        old_path_obj.rename(new_path_obj)
        return format_path(status='success', message=f'Successfully renamed/moved "{old_path}" to "{new_path}"', path=old_path, data={'new_path': str(new_path_obj)})
    except Exception as e:
        return format_path(status='error', message=f'Error: {str(e)}', path=old_path)

@mcp.tool()
async def delete_file(file_path: str) -> str:
    """Delete a file from the directory.

    Args:
        file_path (str): Path of the file to delete. Supports ~ for home directory and relative paths.

    Returns:
        JSON response with:
        - status: 'success' or 'error'
        - message: Operation result description
         - path: Absolute path of file in the directory
        - data: {
            'deleted': True if file was deleted, False otherwise,
            'path': Absolute path of the deleted file
          }
    """
    try:
        path = Path(file_path).expanduser().absolute()
        if not path.exists():
            return format_path(status='error', message=f'Error: file "{file_path}" does not exist', path=file_path)
        path.unlink()
        return format_path(status='success', message=f'Successfully deleted file "{file_path}"', path=file_path, data={'deleted': True, 'path': str(path)})
    except Exception as e: 
        return format_path(status='error', message=f'Error: {str(e)}', path=file_path)

@mcp.tool()
async def deleted_directory(directory_path: str) -> str:
    """Delete a directory from the filesystem.

    Args:
        directory_path (str): Path of the directory to delete. Supports ~ for home directory and relative paths.

    Returns:
        JSON response with:
        - status: 'success' or 'error'
        - message: Operation result description
         - path: Absolute path of directory
        - data: {
            'deleted': True if directory was deleted, False otherwise,
            'path': Absolute path of the deleted directory
          }
    """
    try:
        path = Path(directory_path).expanduser().absolute()
        if not path.exists():
            return format_path(status='error', message=f'Error: directory "{directory_path}" does not exist', path=directory_path)
        if not path.is_dir():
            return format_path(status='error', message=f'Error: directory "{directory_path}" is not a directory', path=directory_path)
        path.rmdir()
        return format_path(status='success', message=f'Successfully deleted directory "{directory_path}"', path=directory_path, data={'deleted': True, 'path': str(path)})
    except Exception as e:
        return format_path(status='error', message=f'Error: {str(e)}', path=directory_path)
    
@mcp.tool()
async def copy_file(source_path: str, destination_path: str) -> str:
    """Copy a file from source to destination.

    Args:
        source_path (str): Path of the file to copy. Supports ~ for home directory and relative paths.
        destination_path (str): Path where the file should be copied to. Supports ~ for home directory and relative paths.    
    
    Returns:
        JSON response with:
        - status: 'success' or 'error'
        - message: Operation result description
         - path: Absolute path of file in the directory
        - data: {
            'copied': True if file was copied, False otherwise,
            'destination': Absolute path of the destination file
          }
    """
    try:
        source_path_obj = Path(source_path).expanduser().absolute()
        destination_path_obj = Path(destination_path).expanduser().absolute()
        if not source_path_obj.exists():
            return format_path(status='error', message=f'Error: file "{source_path}" does not exist', path=source_path) 
        if not source_path_obj.is_file():
            return format_path(status='error', message=f'Error: object "{source_path}" is not a file', path=source_path)
        if destination_path_obj.exists():
            return format_path(status='error', message=f'Error: object "{destination_path}" already exist', path=destination_path)
        shutil.copy2(source_path_obj, destination_path_obj)
        return format_path(status='success', message=f'Successfully copied "{source_path}" to {destination_path}', path=source_path, data={'copied': True, 'destination': str(destination_path_obj)})
    except Exception as e:
        return format_path(status='error', message=f'Error: {str(e)}', path=source_path)
    
@mcp.tool()
async def move_file(source_path: str, destination_path: str) -> str:
    """Move a file from source to destination.

    Args:
        source_path (str): Path of the file to move. Supports ~ for home directory and relative paths.
        destination_path (str): Path where the file should be moved to. Supports ~ for home directory and relative paths.

    Returns:
        JSON response with:
        - status: 'success' or 'error'
        - message: Operation result description
         - path: Absolute path of file in the directory
        - data: {
            'moved': True if file was moved, False otherwise,
            'destination': Absolute path of the destination file      
          }
    """
    try:
        source_path_obj = Path(source_path).expanduser().absolute()
        destination_path_obj = Path(destination_path).expanduser().absolute()
        if not source_path_obj.exists():
            return format_path(status='error', message=f'Error: file "{source_path}" does not exist', path=source_path)
        if not source_path_obj.is_file():
            return format_path(status='error', message=f'Error: object "{source_path}" is not a file', path=source_path)
        if destination_path_obj.exists():
            return format_path(status='error', message=f'Error: object "{destination_path}" already exist', path=destination_path)
        shutil.move(source_path_obj, destination_path_obj)
        return format_path(status='success', message=f'Successfully moved "{source_path}" to {destination_path}', path=source_path, data={'moved': True, 'destination': str(destination_path_obj)})
    except Exception as e:
        return format_path(status='error', message=f'Error: {str(e)}', path=source_path)

@mcp.tool()
async def move_directory(source_path: str, destination_path: str) -> str:
    """Move a directory from source to destination.

    Args:
        source_path (str): Path of the directory to move. Supports ~ for home directory and relative paths.
        destination_path (str): Path where the directory should be moved to. Supports ~ for home directory and relative paths.

    Returns:
        JSON response with:
        - status: 'success' or 'error'
        - message: Operation result description
         - path: Absolute path of directory
        - data: {
            'moved': True if directory was moved, False otherwise,
            'destination': Absolute path of the destination directory
          }
    """
    try:
        source_path_obj = Path(source_path).expanduser().absolute()
        destination_path_obj = Path(destination_path).expanduser().absolute()
        if not source_path_obj.exists():
            return format_path(status='error', message=f'Error: object "{source_path}" does not exist', path=source_path)
        if not source_path_obj.is_dir():
            return format_path(status='error', message=f'Error: object "{source_path}" is not a directory', path=source_path)
        if destination_path_obj.exists():
            return format_path(status='error', message=f'Error: object "{destination_path}" already exist', path=destination_path)
        shutil.move(source_path_obj, destination_path_obj)
        return format_path(status='success', message=f'Successfully moved "{source_path}" to {destination_path}', path=source_path, data={'moved': True, 'destination': str(destination_path_obj)})
    except Exception as e:
        return format_path(status='error', message=f'Error: {str(e)}', path=source_path)
   
@mcp.tool()
async def get_current_directory() -> str:
    """Get the current working directory.

    Args:
        None

    Returns:
        JSON response with:
        - status: 'success'
        - message: Operation result description
        -path: Absolute path of the current directory
        - data: {
            'current_directory': Absolute path of the current directory

          }
    """
    try:
        return format_path(status='success', message='Current directory retrieved successfully', path=str(Path.cwd()), data={'current_directory': str(Path.cwd())})
    except Exception as e:
        return format_path(status='error', message=f'Error: {str(e)}')
@mcp.tool()
async def change_directory(new_path: str) -> str:
    """change the current working directory to a new path.

    Args:
        new_path (str): Path of the directory to change to. Supports ~ for home directory and relative paths.

    Returns:
        JSON response with:
        - status: 'success' or 'error'
        - message: Operation result description
         - path: Absolute path of new directory
        - data: {
            'current_directory': Absolute path of the current directory
          }
    """
    try:
        path = Path(new_path).expanduser().absolute()
        if not path.exists():
            return format_path(status='error', message=f'Error: "{new_path}" does not exist', path=new_path)
        if not path.is_dir():
            return format_path(status='error', message=f'Error: "{new_path}" is not a directory', path=new_path)
        os.chdir(new_path)
        return format_path(status='success', message=f'Successfully changed directory to "{new_path}"', path=new_path, data={'current_directory': str(Path.cwd())})
    except Exception as e:
        return format_path(status='error', message=f'Error: {str(e)}', path=new_path)
    
if __name__ == '__main__':
    mcp.run(transport='stdio')
    