import com.sun.tools.attach.VirtualMachine;
import javax.management.*;import javax.management.remote.*;
public class ReadEffects {
 public static void main(String[] args)throws Exception {
  if(args.length!=1 && !(args.length==5 && "handling-event".equals(args[1])))throw new IllegalArgumentException("Invalid bounded observer arguments");
  VirtualMachine vm=VirtualMachine.attach(args[0]);String address;
  try {address=vm.startLocalManagementAgent();}finally{vm.detach();}
  try(JMXConnector connector=JMXConnectorFactory.connect(new JMXServiceURL(address))){
   MBeanServerConnection m=connector.getMBeanServerConnection();ObjectName name=new ObjectName("lab.fixture:type=Effects");
   if(args.length==1)System.out.println(m.getAttribute(name,"Snapshot"));
   else System.out.println(m.invoke(name,"inspectHandlingEvent",new Object[]{args[2],args[3],args[4]},new String[]{String.class.getName(),String.class.getName(),String.class.getName()}));
  }
 }
}
