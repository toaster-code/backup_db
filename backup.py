import os
from pathlib import Path
import shutil
import datetime
import cmd
from datetime import datetime

BACKUP_PATH = 'c:/Temp/configuration/'


def validate_datetime_format(date_string):
    template = '%Y%m%d_%H%M%S'
    try:
        datetime.strptime(date_string, template)
        return True
    except ValueError:
        return False


class BackupItem():
    """A backup item is a subdirectory inside of the database backup folder.
        The backup item is capable of automatically validating the backup folder
        for the format and the folder contents.
        It allows manipulations like copy, move, delete, etc.
    """
    backup_path = BACKUP_PATH

    def __init__(self, path, comment: str = None) -> None:
        """Initialize a backup item."""
        try:
            # Check if the backup folder is valid(naming, contents,...) so we can initialize the object
            self.check_errors(path, raise_errors=True)
        except ValueError as e:
            raise e
        else:
            # set the relative path to the item as a pathlib.Path object
            self.relative_path = Path(path)
            # initialize the log file (create it if it does not exist)
            self.init_log(comment)

    def init_log(self, comment:str=None):
        """Initialize the log file."""
        log_file = self.path() / 'backup.log'
        # touch the file to allow it to exist
        log_file.touch(exist_ok=True)
        if comment is None:
            # read the comment from the log file
            self.comment = self.write_log(comment)

    def read_log(self):
        """ Read the log file.

        Parameters
        ----------
        comment : str
            The comment to be written to the log file.
            If None, the comment will be read from the log file.

        Returns
        -------
        str
            The contents from the log file.
        """
        log_file = self.path() / 'backup.log'
        with open(log_file, 'r') as log_file:
            return log_file.read()

    def write_log(self, text: str = None):
        """ write the log file.

        Parameters
        ----------
        text : str
            The text to be written to the log file.

        Raises
        ------
        ValueError
            If text is not None and is not a string.
        """

        log_file = self.path() / 'backup.log'
        # touch the file to allow it to exist
        log_file.touch(exist_ok=True)
        with open(log_file, 'w') as log_file:
            log_file.write(text)


    def path(self):
        """Return the absolute path of the backup item."""
        return Path(self.backup_path, self.relative_path)

    @staticmethod
    def is_valid(path: str):
        """Check if the backup item is valid.

        Parameters
        ----------
        path : str
            The backup folder to be validated.

        Returns
        -------
        bool
            True if the backup path is valid, False otherwise.
        """
        try:
            BackupItem.check_errors(path)
        except Exception:
            return False
        else:
            return True

    def is_valid(self):
        """Check if the backup item is valid.

        Returns
        -------
        bool
            True if the backup folder is valid, False otherwise.
        """
        try:
            self.check_errors(self.path)
        except Exception:
            return False
        else:
            return True

    def name(self):
        """Return the backup name."""
        return Path(self.path).name

    @classmethod
    def check_errors(cls, backup_folder: str):
        """Validates that the backup directory is valid.

        The directory to be valid must meet the following criteria:
        - it must be a directory (not a file or a link...)
        - it must be a subfolder of the current backup directory.
        - its name must respect the format 'Backup_YYYYMMDD_HHMMSS', where
            'YYYYMMDD' is a valid date and 'HHMMSS' a valid time (e.g. 20200101_120000).
        - it must contain the following files:
            - Cefor.db (mandatory)
            - Cefor.db-shm (optional)
            - Cefor.db-wal (optional)

        Parameters
        ----------
        backup_folder : str
            The backup folder to be validated.

        Returns
        -------
        bool
            True if the backup folder is valid, False otherwise.
        Raises
        ------
        FileNotFoundError

        """
        # test if backup folder path is absolute or relative
        if Path(backup_folder).is_absolute():
            path = Path(backup_folder)
        else:
            path = Path(cls.BACKUP_PATH, backup_folder)

        # test if path exists
        if not path.exists():
            raise FileNotFoundError(
                f'Backup path {path.absolute()} does not exist.')

        # test if path is really a path to a folder, not a file or a link...
        if not path.is_dir():
            raise NotADirectoryError(
                f'Backup path {path.absolute()} is not a directory.')

        # respects the naming template: path name starts with 'Backup_'
        if not path.name.startswith('Backup_'):
            raise ValueError(
                f'Backup path {path.absolute()} does not respect the naming template.')

        # ends with a date in the format YYYYMMDD-HHMMSS'
        if not validate_datetime_format(path.name.split('Backup_')[-1]):
            raise ValueError(
                f'Backup path {path.absolute()} does not respect the naming template.')

        # directory has valid file contents ('Cefor.db')
        required_file = 'Cefor.db'
        if not Path(path, required_file).exists():
            raise FileNotFoundError(
                f"Backup path {path.absolute()} does not contain a required file: '{required_file}''.")

        # If all tests passed, return None to indicate that the backup folder verification has no errors
        return True


class BackupAgent():
    def __init__(self, path=None) -> None:
        self.backup_path = path if path is not None else BACKUP_PATH

    def item(self, name):
        """Return a backup item by name."""
        return self.list().get(name)

    def list(self, destination_path=None):
        """Create a list of all current backups.
        The list is based on the following criteria:
        - The backup folders must be inside of the backup path, e.g. 'c:/Temp/configuration/'
        - The backup folders must be named in the format 'Backup_YYYYMMDD_HHMMSS', e.g. 'Backup_2020-01-01'
        - The folder contents must contain the following files:
            - Cefor.db (mandatory)
            - Cefor.db-shm (optional)
            - Cefor.db-wal (optional)
            - backup.log (optional)
        - The backup.log file contains the comment for the backup.

        This function then looks into the subfolders of the backup path and checks if the above criteria are met,
        and stores the data into a dict to be manipulated by the Backup Manager.
        """
        # filter items from the backup path that are a directory
        directories = filter(os.path.isdir, os.scandir(self.backup_path))
        # filter the directories that are valid backups
        directories = filter(self.validate_backup_path, directories)

        # Extracting comments from log files
        for directory in directories:
            log_file_path = os.path.join(directory.path, 'backup.log')
            if os.path.exists(log_file_path):
                with open(log_file_path, 'r') as log_file:
                    directory.comment = log_file.read()
            else:
                directory.comment = ''

        return {item.name: item for item in directories}

    def qqvalidate_backup(self, paths):
        """Verify that the backup path is valid.

        The backup path must meet the following criteria:
        - it must be a valid directory.
        - it must be a subfolder of the current working directory.
        - the name of the folder path must respect the format 'Backup_YYYYMMDD_HHMMSS', where
            YYYYMMDD_HHMMSS is a valid date and time (e.g. 20200101_120000)
        - The backup item path must contain the following files:
            - Cefor.db (mandatory)
            - Cefor.db-shm (optional)
            - Cefor.db-wal (optional)
            - backup.log (optional)
        Note: backup.log file contains the comment for the backup.
        """

        # filter by directories
        valid_directories = filter(os.path.isdir, os.scandir(self.backup_path))
        # filter by criteria
        valid_directories = (x for x in valid_directories if (
            # filter directory by a naming template (starting with 'Backup_')
            x.name.startswith('Backup_') and
            # filter directory by a naming template (ending with a date in the format YYYYMMDD-HHMMSS')
            validate_datetime_format(x.name.split('Backup_')[-1]) and
            # filter directories that have valid file contents)
            validate_backup_folder_contents(x.path)))
        return valid_directories


class BackupManager(cmd.Cmd):
    """Command line interface for managing database backups."""

    intro = "Welcome to the Database Backup Manager. Type 'help' to see available commands."
    prompt = ">> "
    backups = {}

    def preloop(self):
        """Load the list of backups when the program starts."""
        self.load_backups()

    def load_backups(self):
        """Load the list of backups from the backup folder."""
        self.backups = {}
        files = os.listdir(BACKUP_PATH)
        for file in files:
            if file.endswith('.db'):
                backup_date = get_backup_date(file)
                if backup_date:
                    self.backups[backup_date] = file

    def display_backups(self):
        """Display a list of all current backups."""
        num_char_comment = 80
        print("Backup List:")
        print("{:<5} {:<20} {:<10} {:<{}}".format(
            "No.", "Name", "Date", "Comment", num_char_comment))
        print("-" * (num_char_comment+40))
        backup_number = 1
        for backup_date, backup_folder in sorted(self.backups.items()):
            backup_name = os.path.basename(backup_folder)
            backup_comment = ''
            log_file_path = os.path.join(backup_folder, 'backup.log')
            if os.path.exists(log_file_path):
                with open(log_file_path, 'r') as log_file:
                    backup_comment = log_file.read(num_char_comment)
            print("{:<5} {:<20} {:<10} {:<{}}".format(
                backup_number, backup_name, backup_date.strftime('%Y-%m-%d'), backup_comment, num_char_comment))
            backup_number += 1
        print("-" * (num_char_comment+40))

    def do_backup(self, line):
        """Create a backup of the database."""
        date = datetime.datetime.now().strftime('%Y-%m-%d')
        comment = input("Enter a comment for the backup (or leave blank): ")
        backup_folder = os.path.join(BACKUP_PATH, date)
        os.makedirs(backup_folder, exist_ok=True)
        for file in ['Cefor.db', 'Cefor.db-shm', 'Cefor.db-wal']:
            shutil.copyfile(os.path.join(BACKUP_PATH, file),
                            os.path.join(backup_folder, file))
        with open(os.path.join(backup_folder, 'backup.log'), 'w') as log_file:
            log_file.write(comment)
        self.backups[datetime.datetime.now()] = backup_folder
        print(f"Backup created successfully: {backup_folder}")

    def do_list(self, line):
        """List all current backups of the database."""
        self.display_backups()

    def do_restore(self, line):
        """Restore a specific version of the database."""
        self.display_backups()
        backup_number = input("Enter the number of the backup to restore: ")
        if backup_number.isdigit():
            backup_number = int(backup_number)
            if 1 <= backup_number <= len(self.backups):
                backup_date = sorted(self.backups.keys())[backup_number - 1]
                backup_folder = self.backups[backup_date]
                confirmation = input(
                    f"Are you sure you want to restore backup '{backup_folder}'? (y/n): ")
                if confirmation.lower() == 'y':
                    # Move current database files to a safe folder
                    safe_folder = os.path.join(BACKUP_PATH, 'safe')
                    os.makedirs(safe_folder, exist_ok=True)
                    for file in ['Cefor.db', 'Cefor.db-shm', 'Cefor.db-wal']:
                        current_file_path = os.path.join(BACKUP_PATH, file)
                        safe_file_path = os.path.join(safe_folder, file)
                        if os.path.exists(current_file_path):
                            shutil.move(current_file_path, safe_file_path)

                    # Restore the selected backup files without overwriting existing files
                    restore_folder = os.path.join(BACKUP_PATH, backup_folder)
                    for file in ['Cefor.db', 'Cefor.db-shm', 'Cefor.db-wal']:
                        backup_file_path = os.path.join(restore_folder, file)
                        destination_file_path = os.path.join(BACKUP_PATH, file)
                        if not os.path.exists(destination_file_path):
                            shutil.copyfile(backup_file_path,
                                            destination_file_path)
                        else:
                            print(
                                f"Error: File '{destination_file_path}' already exists. Skipping restore for this file.")

                    print("Database restored successfully.")
            else:
                print("Invalid backup number.")
        else:
            print("Invalid input. Please enter a number.")

    def parse_backup_numbers(self, backup_numbers_input):
        """Parse the backup numbers input."""
        backup_numbers_input = backup_numbers_input.strip()
        backup_numbers = []
        if backup_numbers_input.isdigit():
            backup_numbers.append(int(backup_numbers_input))
        elif '-' in backup_numbers_input:
            start, end = backup_numbers_input.split('-')
            if start.isdigit() and end.isdigit():
                backup_numbers = list(range(int(start), int(end) + 1))
        return backup_numbers

    def do_delete(self, line):
        """Delete backups by number or range."""
        self.display_backups()
        delete_input = input(
            "Enter the number(s) of the backup(s) to delete (use * for full delete, range with '-'): ")
        delete_input = delete_input.strip()
        if delete_input == '*':
            confirmation = input(
                "Are you sure you want to delete all backups? (y/n): ")
            if confirmation.lower() == 'y':
                print("*" * 80)
                print(
                    "WARNING: This operation is irreversible and will permanently delete the following:")
                print("*" * 80)
                deleted_backups = list(self.backups.values())
                self.backups.clear()
                shutil.rmtree(BACKUP_PATH)
                os.mkdir(BACKUP_PATH)
                print("All backups deleted successfully.\n")
                print("Deleted backups:")
                for backup_folder in deleted_backups:
                    backup_path = os.path.join(BACKUP_PATH, backup_folder)
                    files = os.listdir(backup_path)
                    print(f"\nBackup folder: {backup_path}")
                    for file in files:
                        file_path = os.path.join(backup_path, file)
                        print(f"File: {file_path}")
                print("*" * 80)
        else:
            try:
                backup_numbers = self.parse_backup_numbers(delete_input)
                if backup_numbers:
                    confirm_message = f"Are you sure you want to delete backup(s) {backup_numbers}? (y/n): "
                    confirmation = input(confirm_message)
                    if confirmation.lower() == 'y':
                        print("*" * 80)
                        print(
                            "WARNING: This operation is irreversible and will permanently delete the following:")
                        print("*" * 80)
                        deleted_backups = []
                        for backup_number in backup_numbers:
                            if 1 <= backup_number <= len(self.backups):
                                backup_date = sorted(self.backups.keys())[
                                    backup_number - 1]
                                backup_folder = self.backups[backup_date]
                                print(
                                    f"Are you sure you want to delete the following:")
                                print(f"Backup folder: {backup_folder}")
                                print(
                                    f"Files: {os.listdir(os.path.join(BACKUP_PATH, backup_folder))}")
                                confirm_delete = input("(y/n): ")
                                if confirm_delete.lower() == 'y':
                                    deleted_backups.append(backup_folder)
                                    del self.backups[backup_date]
                                    backup_path = os.path.join(
                                        BACKUP_PATH, backup_folder)
                                    files = os.listdir(backup_path)
                                    print(f"\nBackup folder: {backup_path}")
                                    for file in files:
                                        file_path = os.path.join(
                                            backup_path, file)
                                        print(f"File: {file_path}")
                                    shutil.rmtree(backup_path)
                                    print(
                                        f"\nDeleted backup successfully: {backup_folder}\n")
                                else:
                                    print(
                                        f"Deletion of backup {backup_folder} canceled.\n")
                        print("*" * 80)
                        print("Deleted backups:")
                        for backup in deleted_backups:
                            print(backup)
                        print("*" * 80)
                    else:
                        print("Deletion canceled.")
                else:
                    print("Invalid backup number(s).")
            except ValueError:
                print("Invalid input. Please enter a valid backup number or range.")

    def do_quit(self, line):
        """Quit the program."""
        print("Goodbye!")
        return True


if __name__ == '__main__':
    BackupManager().cmdloop()
