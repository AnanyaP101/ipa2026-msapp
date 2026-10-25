
from netmiko import ConnectHandler
import ntc_templates
import os


def get_interfaces():
    os.environ["NET_TEXTFSM"] = os.path.join(
        os.path.dirname(ntc_templates.__file__),
        "templates"
    )

    device = {
        "device_type": "cisco_ios",
        "host": "10.0.29.101",
        "username": "admin",
        "password": "cisco",
        "conn_timeout": 10,
    }

    try:
        with ConnectHandler(**device) as connection:
            output = connection.send_command(
                "show ip interface brief",
                use_textfsm=True
            )
            print(output)
            return output

    except Exception as error:
        print(f"Router connection failed: {error}")
        return None


if __name__ == "__main__":
    get_interfaces()
