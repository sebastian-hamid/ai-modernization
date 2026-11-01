import com.sun.tools.attach.VirtualMachine;
import javax.management.*;import javax.management.remote.*;
public class ReadEffects {
 public static void main(String[] args)throws Exception {
  if(args.length!=1)throw new IllegalArgumentException("One target PID required");
  VirtualMachine vm=VirtualMachine.attach(args[0]);String address;
  try {address=vm.startLocalManagementAgent();}finally{vm.detach();}
  try(JMXConnector connector=JMXConnectorFactory.connect(new JMXServiceURL(address))){
   System.out.println(connector.getMBeanServerConnection().getAttribute(new ObjectName("lab.fixture:type=Effects"),"Snapshot"));
  }
 }
}
