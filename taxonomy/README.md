# Taxonomy of DCM

This taxonomy of DCM achieves three key goals. First, it defines the top-level domains that distinguish the functions and roles of the DCM architecture. Next, it defines a specific vocabulary with the intent of enabling precision and clarity by eliminating ambiguity. Finally, an "anti-vocabulary" defines a list of ambiguous phrases and "weasel words" to avoid and recommends more specific terms to use instead.

## Top-level architectural domains

The taxonomy defines the functional areas enabled by the DCM architectural as six top-level domains. Each domain maps a set of DCM capabilities defined by the architecture to the different roles and teams across an organization that experience them.

The top-level domains are defined as follows:

0. **Value** - The "zero domain" recognizes the business value achieved through the abstract capabilities enabled by the end-to-end architecture, for example, improved security and compliance, accelerated software deployments and cost saving thanks to reduced operational toil.
1. **Application** - This domain delivers the Unified interface that Developers and Application Owners use to request and manage Services from DCM. It includes the Service Catalog listing the available Services. Multi-tenancy is experienced at this level.
2. **Control Plane** - This is the central nervous system of DCM. It maintains the Unified API and Data Model including the inventory of Fulfilled Services. It also implements the authentication and role-based access control required to enforce multi-tenancy.
3. **Resource** - This domain contains the code and workflows for provisioning and managing the resources required to Fulfill Service request. It provides the engines that execute requests from the Control Plane and translates those into API calls supported by specific Infrastructure Platforms hosted under the Data Center domain.
4. **Data Center** - This domain represents the physical and virtual composable infrastructure in the data center. This is where the basic compute, storage and networking resources are provisioned.
5. **Governance & FinOps** - This domain is the set of overarching requirements that ensure DCM operations are secure, compliant, and cost-effective. It encompasses policy management, real-time metrics, and cost allocation.

Everything in the DCM architecture exists under one of these domains.

How these domains are connected can be easily understood using a layer cake analogy.

![Layer cake analogy drawing described below](./images/layer_cake.png)

Each layer of cake represents a domain that interacts only with the domains directly above and below it. For example, the architecture prohibits a direct connection from the Application domain to the Resource domain, Instead, capabilities under the Application domain must always use the Control Plane to request and manage resources available from the lower domains.

The exception to this rule is the Governance & FinOps domain. It is the frosting of our cake and it touches all the layers. This aligns with the overarching functions of the Governance & FinOps domain requiring observability at every level of the architecture.

## Vocabulary

DCM is a complex technology architecture stretching from the depths of bare metal on the data center floor up to the high-level abstractions required to achieve secure multi-tenancy in the service of cloud consuming application owners and developers.

The vocabulary we use to define this architecture demands precision and clarity. By allowing a term to have a distinct, contextual definition within each architectural domain, we can eliminating ambiguity even when using the same words.

For example, the "resource" a developer requests for their application is a logical entity, for example, a "Web App Service." However, the "resource" that the Infrastructure Operations team manages is a physical asset like a specific VM with a particular IP address. By providing distinct definitions for the same term in each domain, we avoid confusion as we navigate through the architectural domains.

When adding new terms to the vocabulary, take care to map the terms to the roles and functions relevant to each applicable domain.

### Application

An Application is a defined collection of Services configured to deploy a self-contained software solution designed to meet a specific business purpose. An Application is full-stack product typically including a front-end user interface, business logic, data storage, and potentially network interfaces to other Applications.

### Data Model

The Data Model defines the scope of Unified Data within the Control Plane. The Data Model includes static data as well as event data such as the history of Fulfilled Service requests and time series data such as Workload usage metrics. Data Model does not mean database, but rather is a broader term meaning the scope of any data supporting the DCM architecture. While Static Data may be stored using a traditional database service, Event Data from Service requests could be better sent to a logging service and Usage Metrics Data might be more suitably captured and stored using a time series data platform.

Code may also be considered in the scope of the Data Model such as the Infrastructure-as-Code used to define Compound Services and should be managed using GitOps practices.

Dynamic Data also falls under the scope of the Data Model, for example, the current state of a provisioned resource. Dynamic Data can be directly queried using the Unified API and it may also be cached.

### Infrastructure Platform

Infrastructure Platforms refer to the Data Center infrastructure and platforms that provide resources within the Data Center domain. An Infrastructure Platform may be physical hardware or a software platform, for example, bare metal servers, network gear, storage arrays, virtualization platforms, Kubernetes clusters, etc. Each Infrastructure Platform defines the physical and/or virtual resources it supports, such as compute, storage, network, VM instances, Kubernetes cluster objects, etc.

An Infrastructure Platform provides an API used by a Service Provider to provision, decommission, make state changes to and enable discovery of the resources it supports. Infrastructure Platforms must also expose event logging and metrics collection to the Governance & FinOps domain required to support monitoring, observability and billing.

### Multi-tenant

DCM multi-tenancy is experienced at the Application domain and enforced by the Control Plane.

The Resource and Data Center domains operate in "privileged mode" to implement the isolation and confinement required for multi-tenancy.

The Governance & FinOps domain has access to the tenant-wide scope required to implement policy management, monitoring and billing.

### Placement

Workload Placement policies are managed within the Governance & FinOps domain and enforced within the Control Plane domain.

### Region

A Region is a large, geographically distinct area that hosts resources. It can be a single Data Center or a group of Data Centers in close proximity. Regions should be designed as physically and logically independent from other Regions. This design is crucial for disaster recovery and business continuity, so a failure in one region doesn't affect another.

### Service

A Service is the specific capability supported by a Service Catalog item within the Application domain. Services provide the underlying resources that Applications rely on.

Service Catalog items supporting Atomic Services are defined by Service Providers and tightly coupled to a provided resource. Compound Services can be defined to provides a configuration of any combination of Atomic Services making it possible for a single Service Catalog item to provide arbitrarily complex Application environments.

### Service Provider

Service Providers support provisioning and management of resources required to Fulfill Service requests from the Control Plane in a way that is agnostic to the implementations of different Infrastructure Platforms. Service Providers implement the Naturalization required to translate Unified API requests from the Control Plane into an Infrastructure Platform's native API and the Denaturalization required to translate native API responses into responses that comply with the Unified API.

Service Providers will typically be implemented to support a single specific Infrastructure Platform. However, a Service Provider could also be implemented to support a class of Infrastructure Platforms, for example, one Service Provider supporting a number of different virtualization platforms.

To support Fulfillment of Service requests requiring any resources they provide, Service Providers define the Service Catalog items for those resources to be exposed by the Control Plane.

### User

In the absence of further context, the User is the human consumer of cloud computing Services experiencing DCM within the Application domain using the APIs (or Web UI) of the Control Plane. Of course, other humans "use" DCM within the other domains, so consider more specific terms like Developer or Application Owner instead.

To avoid confusion, refrain from saying User when referring to humans acting within the the other DCM domains. Consider more specific persona alternative terms such as Platform Engineer, Infrastructure Operations, Policy Owner, Risk and Compliance Manager, etc.

### Workload

A Workload is a running instance of a Service that has been Fulfilled at the request of a User in the Application domain. A Workload is composed of the provisioned resources required by the Service. The State and usage of the Workload's resources are monitored by tools in the Governance & FinOps domain to enable observability and billing for Services.

### Zone

Also known as an Availability Zone, a Zone is an isolated group of resources within a Region. Each Region consists of one or more Zones. A Zone is a separate physical facility with its own power, cooling, and networking, ensuring that a problem in one Zone, like a power outage or a localized fire, doesn't impact other Zones in the same Region. By deploying resources across multiple Zones within a single Region, high availability and fault tolerance can be achieved for Services and Applications. Zones are defined by Infrastructure Platforms and can be namespaces, clusters or anything that results in its resources being isolated as spelled out above.

## Anti-vocabulary

The goal of the anti-vocabulary is to encourage clarity and discipline in technical communication by pointing out ambiguous terms to avoid while explaining the concrete reasons and offering clear alternatives to consider instead.

### Data Center

The term Data Center is somewhat irrelevant from a DCM architecture perspective. It is simply a building that provides the roof over an arbitrary collection of physical infrastructure. Consider using the more architecturally meaningful terms Region and Zone.

### Realize

To realize can mean to bring something into existence, to make something intangible less so, to achieve a goal, or even just to understand as in "Ah, now I realize what's going on." Given all these meanings, avoid using this word. Consider more precise words like provision as in a VM, install as in a software package, fulfill as in a request, etc.

### Tangible

Nothing in the DCM architecture is intangible. Tangible and intangible are weasel words that sound important but don't add any clarity or meaning. Avoid using these words.

### Widgets

Widget are things, but what things exactly? Rather than saying widgets, find the precise word for the resource or service for the thing you are talking about.
