import { BrowserRouter, Route, Routes } from "react-router-dom";
import Lobby from "./pages/Lobby";
import Settings from "./pages/Setttings";
import KnowledgeBases from "./pages/KnowledgeBases";
import AboutAusma from "./pages/AboutAusma";
import ChatWrapper from "./pages/Chat";
import { useLocalStorageState } from "./utils/useLocalStorageState";
import Layout from "./components/Layout";
import { UsernameContext } from "./components/UserName";

export default function App() {
  const [username, setUsername] = useLocalStorageState("username", "Anonymous");
  return (
    <>
      <BrowserRouter>
        {/* Where Updating the routes remember to update flask_app.host_frontend in the backend python code. */}
        <UsernameContext.Provider value={{ username, setUsername }}>
          <Layout username={username} >
            {({ setClosed }) => (
              <Routes>
                <Route path="/" element={<Lobby setClosed={setClosed} />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/knowledge-base" element={<KnowledgeBases />} />
                <Route path="/about" element={<AboutAusma />} />
                <Route path="/chat/:room" element={<ChatWrapper />} />
              </Routes>
            )}
          </Layout>
        </UsernameContext.Provider>
      </BrowserRouter>
    </>
  );
}
