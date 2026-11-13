import { Link, Route, Routes } from "react-router-dom";
function Home(){return <main className="container"><h1>Retina Screening</h1><p>Research screening-support prototype.</p><Link to="/screening">Start screening</Link></main>}
function Screening(){return <main className="container"><h1>Screening</h1><p>Image upload workflow is a development task.</p></main>}
export default function App(){return <Routes><Route path="/" element={<Home/>}/><Route path="/screening" element={<Screening/>}/><Route path="*" element={<Home/>}/></Routes>}
