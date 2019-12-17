# Proyecto Plataforma de Agentes

## Autores:
### Leonel Alejandro García López
### Roberto Marti Cedeño

Estre proyecto de plataforma de agentes pretende dar una solucion distribuida al problema planteado,
esta plataforma de agentes basa su funcionamiento en 5 componentes listadas a continuación:

* Cliente

* Message_Handler

* Message_Resolver

* Direcotry Facilitator

* AMS

#### Cliente
 Nuestro cliente de la plataforma de agentes posee varias funcionalidades y su mayor importancia recae en que es la entidad que se encarga de adicionar o consultar registros a la misma. Además esta construido sobre la biblioteca cmd de python y tiene una funcionalidad adicional de levantar un socket local para la comunicación transparente con el servicio pedido

#### Message_Handler
 Primera entidad de la sección de mensajería de la plataforma, posee dos servidores que responden a las peticiones de 
 los clientes y los Message_Resolvers, ademas responde también a los pedidos de descubrimiento de los mismos.

#### Message_Resolver
 Entidad de la plataforma que se encarga de realizar los pedidos entrantes, por cada pedido que obtiene de algun Message_Handler, resuleve las consultas pertinentes tanto en el AMS como el DF.

#### Direcotry Facilitator
 Base de datos compartida, que trabaja sobre RAM cuya principal propiedad radica en rapida recuperación de errores y 
estrategia de tolerancia a fallos de tipo crash y replicación de grado 2.

#### AMS
 DHT basado en kademlia pero con variaciones y sin abarcar la totalidad del algoritmo, no utilizamos la republicación de (llave, valores),en cuanto a los tiempos y como tradicionalmente se implementa, es distinto, se utilizó rpc y en este caso rpyc por sus facilidades. Con laas constantes del algoritmo identicas a excepcón del alpha=1 para aumentar la velocidad ya que en el caso de python es demasiado lento el cambio de contexto. Usamos una capa de abstracción para esta red kademlia y le llamamos AgentManager(Servicio de rpyc al igual que kademlia y que hereda del mismo tipo Service) para facilitar el acceso a los datos desde entidades ajenas a la red. Desde la creación de la instancia de nodo kademlia mantenemos una hebra q se encarga de eliminar la las entradas antiguas.
 
##### Registro de Agentes en la PLataforma
Para Registrar un agente a la plataforma se debe crear un archivo con sinstaxis yaml que tenga los siguientes campos:

* ip

* port

* url

* protocol

* service

Preferiblemente estos archivos deben ser ubicados en la carpeta ../Templates del directorio donde se ejecuta el cliente.
