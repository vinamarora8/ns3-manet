/*
 * Copyright (c) 2011 University of Kansas
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * Author: Justin Rohrer <rohrej@ittc.ku.edu>
 *
 * James P.G. Sterbenz <jpgs@ittc.ku.edu>, director
 * ResiliNets Research Group  https://resilinets.org/
 * Information and Telecommunication Technology Center (ITTC)
 * and Department of Electrical Engineering and Computer Science
 * The University of Kansas Lawrence, KS USA.
 *
 * Work supported in part by NSF FIND (Future Internet Design) Program
 * under grant CNS-0626918 (Postmodern Internet Architecture),
 * NSF grant CNS-1050226 (Multilayer Network Resilience Analysis and Experimentation on GENI),
 * US Department of Defense (DoD), and ITTC at The University of Kansas.
 */

/*
 * This example program allows one to run ns-3 DSDV, AODV, or OLSR under
 * a typical random waypoint mobility model.
 *
 * By default, the simulation runs for 200 simulated seconds, of which
 * the first 50 are used for start-up time.  The number of nodes is 50.
 * Nodes move according to RandomWaypointMobilityModel with a speed of
 * 20 m/s and no pause time within a 300x1500 m region.  The WiFi is
 * in ad hoc mode with a 2 Mb/s rate (802.11b) and a Friis loss model.
 * The transmit power is set to 7.5 dBm.
 *
 * It is possible to change the mobility and density of the network by
 * directly modifying the speed and the number of nodes.  It is also
 * possible to change the characteristics of the network by changing
 * the transmit power (as power increases, the impact of mobility
 * decreases and the effective density increases).
 *
 * By default, OLSR is used, but specifying a value of 2 for the protocol
 * will cause AODV to be used, and specifying a value of 3 will cause
 * DSDV to be used.
 *
 * By default, there are 10 source/sink data pairs sending UDP data
 * at an application rate of 2.048 Kb/s each.    This is typically done
 * at a rate of 4 64-byte packets per second.  Application data is
 * started at a random time between 50 and 51 seconds and continues
 * to the end of the simulation.
 *
 * The program outputs a few items:
 * - packet receptions are notified to stdout such as:
 *   <timestamp> <node-id> received one packet from <src-address>
 * - each second, the data reception statistics are tabulated and output
 *   to a comma-separated value (csv) file
 * - some tracing and flow monitor configuration that used to work is
 *   left commented inline in the program
 */

#include "ns3/aodv-module.h"
#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/dsdv-module.h"
#include "ns3/dsr-module.h"
#include "ns3/internet-module.h"
#include "ns3/mobility-module.h"
#include "ns3/network-module.h"
#include "ns3/olsr-module.h"
#include "ns3/yans-wifi-helper.h"
#include "ns3/flow-monitor-helper.h"

#include <fstream>
#include <iostream>

using namespace ns3;
using namespace dsr;

std::string packetSize = "64";
int nodeSpeed = 0; // in m/s
double pauseTime = 3;  // in s
NS_LOG_COMPONENT_DEFINE("manet");
int seed = 1234;
int offtime = 0.0;

/**
 * Routing experiment class.
 *
 * It handles the creation and run of an experiment.
 */
class RoutingExperiment
    {
    public:
        RoutingExperiment();

        void Run(double txp, std::string CSVfileName);


        std::string CommandSetup(int argc, char** argv);

        void WriteSimState();

    private:
        Ptr<Socket> SetupPacketReceive(Ipv4Address addr, Ptr<Node> node);

        void ReceivePacket(Ptr<Socket> socket);


        void CheckThroughput();

        uint32_t port;            //!< Receiving port number.
        uint32_t bytesTotal;      //!< Total received bytes.
        uint32_t packetsReceived; //!< Total received packets.
        uint32_t totPacketsReceived; //!< Total received packets.

        std::string m_CSVfileName;  //!< CSV filename.
        int m_nSinks;               //!< Number of sink nodes.
        int m_nWifi;
        std::string m_protocolName; //!< Protocol name.
        double m_txp;               //!< Tx power.
        bool m_traceMobility;       //!< Enavle mobility tracing.
        uint32_t m_protocol;        //!< Protocol type.
        NodeContainer adhocNodes;
        std::string stateFname;
        double kbs;
    };

RoutingExperiment::RoutingExperiment()
    : port(9),
    bytesTotal(0),
    packetsReceived(0),
    totPacketsReceived(0),
    m_CSVfileName("manet-routing.output.csv"),
    m_nWifi(50),
    m_traceMobility(false),
    m_protocol(2), // AODV
    stateFname("manet-state.txt"),
    kbs(0.0)
{
}

static inline std::string
PrintReceivedPacket(Ptr<Socket> socket, Ptr<Packet> packet, Address senderAddress)
{
    std::ostringstream oss;

    oss << Simulator::Now().GetSeconds() << " " << socket->GetNode()->GetId();

    if (InetSocketAddress::IsMatchingType(senderAddress))
        {
            InetSocketAddress addr = InetSocketAddress::ConvertFrom(senderAddress);
            oss << " received one packet from " << addr.GetIpv4();
        }
    else
    {
        oss << " received one packet!";
    }
    return oss.str();
}

void
RoutingExperiment::ReceivePacket(Ptr<Socket> socket)
{
    Ptr<Packet> packet;
    Address senderAddress;
    while ((packet = socket->RecvFrom(senderAddress)))
    {
        bytesTotal += packet->GetSize();
        packetsReceived += 1;
        totPacketsReceived += 1;
        //NS_LOG_UNCOND(PrintReceivedPacket(socket, packet, senderAddress));
    }
}

Vector getNodePosition(Ptr<Node> n)
{
    return n->GetObject<MobilityModel>()->GetPosition();
}


void RoutingExperiment::WriteSimState()
{
    Simulator::Schedule(Seconds(1.0), &RoutingExperiment::WriteSimState, this);

    double time = Simulator::Now().GetSeconds();
    if (time < 100)
    {
        return;
    }

    int numNodes = adhocNodes.GetN();

    std::ofstream outfile(stateFname, std::ios_base::app);
    outfile << "TIME " << time << std::endl;
    outfile << "NUM_NODES " << numNodes << std::endl;
    outfile << "NUM_SINKS " << m_nSinks << std::endl;
    outfile << "THROUGHPUT " << kbs << std::endl;
    outfile << "POSITIONS" << std::endl;
    for (int i = 0; i < numNodes; i++)
    {
        Vector pos = getNodePosition(adhocNodes.Get(i));
        outfile << i << " " << pos.x << " " << pos.y << " " << pos.z << std::endl;
    }
    outfile.close();
}


void
RoutingExperiment::CheckThroughput()
{
    //WriteSimState();
    kbs = (bytesTotal * 8.0) / 1000;
    bytesTotal = 0;

    std::ofstream out(m_CSVfileName, std::ios::app);

    out << (Simulator::Now()).GetSeconds() << "," << kbs << "," << packetsReceived << ","
        << m_nSinks << "," << m_protocolName << "," << m_txp << "" << std::endl;

    out.close();
    packetsReceived = 0;
    Simulator::Schedule(Seconds(1.0), &RoutingExperiment::CheckThroughput, this);
}

Ptr<Socket>
RoutingExperiment::SetupPacketReceive(Ipv4Address addr, Ptr<Node> node)
{
    TypeId tid = TypeId::LookupByName("ns3::UdpSocketFactory");
    Ptr<Socket> sink = Socket::CreateSocket(node, tid);
    InetSocketAddress local = InetSocketAddress(addr, port);
    sink->Bind(local);
    sink->SetRecvCallback(MakeCallback(&RoutingExperiment::ReceivePacket, this));

    return sink;
}

std::string
RoutingExperiment::CommandSetup(int argc, char** argv)
{
    CommandLine cmd(__FILE__);
    cmd.AddValue("CSVfileName", "The name of the CSV output file name", m_CSVfileName);
    cmd.AddValue("traceMobility", "Enable mobility tracing", m_traceMobility);
    cmd.AddValue("protocol", "1=OLSR;2=AODV;3=DSDV;4=DSR", m_protocol);
    cmd.AddValue("nSinks", "Number of sink nodes", m_nSinks);
    cmd.AddValue("nWifi", "Total number of nodes", m_nWifi);
    cmd.AddValue("pauseTime","pause time for the nodes",pauseTime);
    cmd.AddValue("nodeSpeed","Speed of the nodes while moving in Random WayPoint",nodeSpeed);
    cmd.AddValue("packetSize","Packet Size",packetSize);
    cmd.AddValue("seed","seed",seed);
    cmd.Parse(argc, argv);

    std::ofstream outfile(stateFname, std::ios_base::out);
    outfile.close();
    return m_CSVfileName;
}

int
main(int argc, char* argv[])
{
    RoutingExperiment experiment;
    std::string CSVfileName = experiment.CommandSetup(argc, argv);

    // blank out the last output file and write the column headers
    std::ofstream out(CSVfileName);
    out << "SimulationSecond,"
        << "ReceiveRate,"
        << "PacketsReceived,"
        << "NumberOfSinks,"
        << "RoutingProtocol,"
        << "TransmissionPower" << std::endl;
    out.close();

    double txp =2 *7.5; // Can shmooo this....

    experiment.Run(txp, CSVfileName);

    return 0;
}

void
RoutingExperiment::Run(double txp, std::string CSVfileName)
{
    RngSeedManager::SetSeed(seed);

    Packet::EnablePrinting();
    m_txp = txp;
    m_CSVfileName = CSVfileName;
    double pl_exp = 1.75; // Using the best value for gamma from my experiments...

    int nWifis = m_nWifi;

    double TotalTime = 200.0;
    // TODO Rate changes. Looks too low
    std::string rate("2048bps");

    std::string phyMode("VhtMcs7"); 

    std::string tr_name("manet-routing-compare");
    m_protocolName = "protocol";

    Config::SetDefault("ns3::OnOffApplication::PacketSize", StringValue(packetSize));
    Config::SetDefault("ns3::OnOffApplication::DataRate", StringValue(rate));

    // Set Non-unicastMode rate to unicast mode
    Config::SetDefault("ns3::WifiRemoteStationManager::NonUnicastMode", StringValue(phyMode));

    adhocNodes.Create(nWifis);

    // setting up wifi phy and channel using helpers
    WifiHelper wifi;
    wifi.SetStandard(WIFI_STANDARD_80211ac); // Changing the standard to 802.11 ac as its the latest one
    //
    uint32_t rtsThreshold = 65535; 


    YansWifiPhyHelper wifiPhy;
    YansWifiChannelHelper wifiChannel;
    wifiChannel.SetPropagationDelay("ns3::ConstantSpeedPropagationDelayModel");
    wifiChannel.AddPropagationLoss ("ns3::LogDistancePropagationLossModel", "Exponent", DoubleValue(pl_exp));


    wifiPhy.SetChannel(wifiChannel.Create());
    // Standard parameters taken from Lab4 asssignemtns
    std::string frequencyBand;
    uint32_t chWidth = 20;
    frequencyBand = "BAND_5GHZ"; // 802.11 ac predominantly works for 5Ghz

    wifiPhy.Set("ChannelSettings",
                StringValue("{0, " + std::to_string(chWidth) + ", " + frequencyBand + ", 0}"));

    // Add a mac and disable rate control
    WifiMacHelper wifiMac;

    wifi.SetRemoteStationManager("ns3::MinstrelHtWifiManager", "RtsCtsThreshold", UintegerValue(rtsThreshold));
    //  wifi.SetRemoteStationManager("ns3::ConstantRateWifiManager",
    //                               "DataMode",
    //                               StringValue(phyMode),
    //                               "ControlMode",
    //                               StringValue(phyMode));
    wifiPhy.Set("TxPowerStart", DoubleValue(txp)); // Worried if this makes sense when we have a minstrel rate algo. But lets see.
    wifiPhy.Set("TxPowerEnd", DoubleValue(txp));

    wifiMac.SetType("ns3::AdhocWifiMac");
    NetDeviceContainer adhocDevices = wifi.Install(wifiPhy, wifiMac, adhocNodes);
    //    uint32_t BeMaxAmpduSize = 65535;
    //    Config::Set("/NodeList/*/DeviceList/*/$ns3::WifiNetDevice/Mac/BE_MaxAmpduSize",
    //                    UintegerValue(BeMaxAmpduSize));
    //    bool shortGuardInterval = false; 
    //    // Set guard interval
    //    Config::Set(
    //        "/NodeList/*/DeviceList/*/$ns3::WifiNetDevice/HtConfiguration/ShortGuardIntervalSupported",
    //        BooleanValue(shortGuardInterval));

    MobilityHelper mobilityAdhoc;
    int64_t streamIndex = 0; // used to get consistent mobility across scenarios

    ObjectFactory pos;
    pos.SetTypeId("ns3::RandomRectanglePositionAllocator");
    pos.Set("X", StringValue("ns3::UniformRandomVariable[Min=0.0|Max=1000.0]"));
    pos.Set("Y", StringValue("ns3::UniformRandomVariable[Min=0.0|Max=1000.0]"));

    Ptr<PositionAllocator> taPositionAlloc = pos.Create()->GetObject<PositionAllocator>();
    streamIndex += taPositionAlloc->AssignStreams(streamIndex);

    std::stringstream ssSpeed;
    //ssSpeed << "ns3::ConstantRandomVariable[Constant=" << nodeSpeed << "]"; 
    ssSpeed << "ns3::UniformRandomVariable[Min="<< 0.5*nodeSpeed << "|Max=" << nodeSpeed << "]";
    std::stringstream ssPause; 
    //ssPause << "ns3::ConstantRandomVariable[Constant=" << pauseTime << "]"; //"ns3::UniformRandomVariable[Min="<< pauseTime << "|Max=["<<pauseTime <<"]"; //"ns3::UniformRandomVariable[Min=0.0|Max=20.0]";
    ssPause << "ns3::UniformRandomVariable[Min=0.0|Max="<<pauseTime <<"]"; //"ns3::UniformRandomVariable[Min=0.0|Max=20.0]";
    mobilityAdhoc.SetMobilityModel("ns3::RandomWaypointMobilityModel",
                                   "Speed",
                                   StringValue(ssSpeed.str()),
                                   "Pause",
                                   StringValue(ssPause.str()),
                                   "PositionAllocator",
                                   PointerValue(taPositionAlloc));
    mobilityAdhoc.SetPositionAllocator(taPositionAlloc);
    mobilityAdhoc.Install(adhocNodes);
    streamIndex += mobilityAdhoc.AssignStreams(adhocNodes, streamIndex);

    AodvHelper aodv;
    OlsrHelper olsr;
    DsdvHelper dsdv;
    InternetStackHelper internet;
    Ipv4ListRoutingHelper list;
    switch (m_protocol)
    {
        case 1:
            list.Add(olsr, 100);
            m_protocolName = "OLSR";
            break;
        case 2:
            list.Add(aodv, 100);
            m_protocolName = "AODV";
            break;
        case 3:
            list.Add(dsdv, 100);
            m_protocolName = "DSDV";
            break;
        default:
            NS_FATAL_ERROR("No such protocol:" << m_protocol);
    }

    if (m_protocol < 4)
    {
        internet.SetRoutingHelper(list);
        internet.Install(adhocNodes);
    }

    NS_LOG_INFO("assigning ip address");

    Ipv4AddressHelper addressAdhoc;
    addressAdhoc.SetBase("10.1.1.0", "255.255.255.0");
    Ipv4InterfaceContainer adhocInterfaces;
    adhocInterfaces = addressAdhoc.Assign(adhocDevices);
    OnOffHelper onoff1("ns3::UdpSocketFactory", Address());
    onoff1.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1.0]"));
    onoff1.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0.0]"));
    for (int i = 0; i < m_nSinks; i++)
    {
        Ptr<Socket> sink = SetupPacketReceive(adhocInterfaces.GetAddress(i), adhocNodes.Get(i));

        AddressValue remoteAddress(InetSocketAddress(adhocInterfaces.GetAddress(i), port));
        onoff1.SetAttribute("Remote", remoteAddress);

        Ptr<UniformRandomVariable> var = CreateObject<UniformRandomVariable>();
        ApplicationContainer temp = onoff1.Install(adhocNodes.Get(i + m_nSinks));
        temp.Start(Seconds(var->GetValue(100.0, 101.0)));
        temp.Stop(Seconds(TotalTime));
    }

    std::stringstream ss;
    ss << nWifis;
    std::string nodes = ss.str();

    std::stringstream ss2;
    ss2 << nodeSpeed;
    std::string sNodeSpeed = ss2.str();

    std::stringstream ss3;
    ss3 << pauseTime;
    std::string sNodePause = ss3.str();

    std::stringstream ss4;
    ss4 << rate;
    std::string sRate = ss4.str();
    // NS_LOG_INFO("Configure Tracing.");
    //tr_name = tr_name + "_" + m_protocolName +"_" + nodes + "nodes_" + sNodeSpeed + "speed_" +
    //sNodePause + "pause_" + sRate + "rate";

    AsciiTraceHelper ascii;
    Ptr<OutputStreamWrapper> osw = ascii.CreateFileStream(tr_name + ".tr");
    wifiPhy.EnableAsciiAll(osw);
    //MobilityHelper::EnableAsciiAll(ascii.CreateFileStream(tr_name + ".mob"));

    Ptr<FlowMonitor> flowmon;
    FlowMonitorHelper flowmonHelper;
    flowmon = flowmonHelper.InstallAll();

    NS_LOG_INFO("Run Simulation.");

    CheckThroughput();
    WriteSimState();

    // Routing setup time
    Simulator::Stop(Seconds(99));
    Simulator::Run();

    Ptr<OutputStreamWrapper> routingStream = Create<OutputStreamWrapper>("manet-rtable.txt", std::ios::out);
    list.PrintRoutingTableAllEvery(Seconds(1.0), routingStream);

    // Main simulation
    Simulator::Stop(Seconds(TotalTime - 101));
    Simulator::Run();

    flowmon->CheckForLostPackets();
    flowmon->SerializeToXmlFile(tr_name + ".flowmon", false, false);
    Simulator::Destroy();

    //std::cout << "Total packets received " << totPacketsReceived << std::endl;
}

