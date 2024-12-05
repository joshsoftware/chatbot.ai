import Chat from "@/components/chat";

const Home = () => {
  return (
    <main className="flex justify-center items-center h-screen bg-white">
      <div className="max-w-lg w-full h-full">
        <Chat />
      </div>
    </main>
  );
};

export default Home;