from getpass import getpass
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError

class Command(BaseCommand):
    help = "交互式创建内部或外部账号，不通过命令行传递密码"
    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("--internal", action="store_true")
    def handle(self, *args, **options):
        if get_user_model().objects.filter(username=options["username"]).exists():
            raise CommandError("账号已存在")
        user = get_user_model()(username=options["username"], is_staff=options["internal"])
        password=getpass("密码：")
        if password != getpass("再次输入："):
            raise CommandError("两次密码不一致")
        try: validate_password(password, user)
        except ValidationError as error: raise CommandError("；".join(error.messages))
        user.set_password(password); user.save()
        self.stdout.write(self.style.SUCCESS("账号已创建"))
