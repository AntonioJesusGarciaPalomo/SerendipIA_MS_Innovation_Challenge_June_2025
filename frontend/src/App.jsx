import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, Send, Paperclip } from 'lucide-react';
import axios from 'axios';
import './App.css';

function App() {
    const [messages, setMessages] = useState([]);
    const [inputMessage, setInputMessage] = useState('');
    const [uploadedFiles, setUploadedFiles] = useState([]);
    const [isUploading, setIsUploading] = useState(false);

    const onDrop = useCallback(async (acceptedFiles) => {
        setIsUploading(true);

        for (const file of acceptedFiles) {
            try {
                const formData = new FormData();
                formData.append('file', file);

                const response = await axios.post('/api/upload', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                });

                setUploadedFiles(prev => [...prev, {
                    name: file.name,
                    size: file.size,
                    blobName: response.data.blob_name,
                    uploadTime: new Date().toISOString()
                }]);

                // Add system message about successful upload
                setMessages(prev => [...prev, {
                    type: 'system',
                    content: `📎 Archivo "${file.name}" cargado exitosamente`,
                    timestamp: new Date().toISOString()
                }]);

            } catch (error) {
                console.error('Error uploading file:', error);
                setMessages(prev => [...prev, {
                    type: 'error',
                    content: `❌ Error al cargar "${file.name}": ${error.response?.data?.detail || error.message}`,
                    timestamp: new Date().toISOString()
                }]);
            }
        }

        setIsUploading(false);
    }, []);

    const { getRootProps, getInputProps, open } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
            'application/msword': ['.doc'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            'application/vnd.ms-excel': ['.xls'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
            'application/vnd.ms-powerpoint': ['.ppt'],
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx']
        },
        noClick: true,
        noKeyboard: true
    });

    const handleSendMessage = () => {
        if (inputMessage.trim()) {
            setMessages(prev => [...prev, {
                type: 'user',
                content: inputMessage,
                timestamp: new Date().toISOString()
            }]);

            // Simulate assistant response
            setTimeout(() => {
                setMessages(prev => [...prev, {
                    type: 'assistant',
                    content: 'Sistema RAG en desarrollo. Los archivos se han almacenado correctamente en Azure Blob Storage.',
                    timestamp: new Date().toISOString()
                }]);
            }, 1000);

            setInputMessage('');
        }
    };

    const removeFile = (index) => {
        setUploadedFiles(prev => prev.filter((_, i) => i !== index));
    };

    return (
        <div className="flex flex-col h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 px-6 py-4">
                <h1 className="text-xl font-semibold text-gray-800">RAG Document Assistant</h1>
                <p className="text-sm text-gray-500">Sube documentos y haz preguntas</p>
            </header>

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto p-6" {...getRootProps()}>
                <input {...getInputProps()} />

                {messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-gray-400">
                        <Upload className="w-16 h-16 mb-4" />
                        <p className="text-lg mb-2">Arrastra archivos aquí o usa el botón de adjuntar</p>
                        <p className="text-sm">Formatos soportados: PDF, Word, Excel, PowerPoint</p>
                    </div>
                ) : (
                    <div className="space-y-4 max-w-3xl mx-auto">
                        {messages.map((msg, index) => (
                            <div
                                key={index}
                                className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                                <div
                                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${msg.type === 'user'
                                            ? 'bg-blue-500 text-white'
                                            : msg.type === 'error'
                                                ? 'bg-red-100 text-red-700'
                                                : msg.type === 'system'
                                                    ? 'bg-gray-100 text-gray-700'
                                                    : 'bg-white text-gray-800 border border-gray-200'
                                        }`}
                                >
                                    {msg.content}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Uploaded Files */}
            {uploadedFiles.length > 0 && (
                <div className="px-6 py-3 bg-gray-100 border-t border-gray-200">
                    <div className="flex flex-wrap gap-2">
                        {uploadedFiles.map((file, index) => (
                            <div
                                key={index}
                                className="flex items-center gap-2 bg-white px-3 py-1 rounded-full border border-gray-300"
                            >
                                <File className="w-4 h-4 text-gray-500" />
                                <span className="text-sm text-gray-700">{file.name}</span>
                                <button
                                    onClick={() => removeFile(index)}
                                    className="text-gray-400 hover:text-gray-600"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Input Area */}
            <div className="border-t border-gray-200 bg-white px-6 py-4">
                <div className="flex items-center gap-3 max-w-3xl mx-auto">
                    <button
                        onClick={open}
                        disabled={isUploading}
                        className="p-2 text-gray-500 hover:text-gray-700 disabled:opacity-50"
                        title="Adjuntar archivo"
                    >
                        <Paperclip className="w-5 h-5" />
                    </button>

                    <input
                        type="text"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                        placeholder="Escribe un mensaje..."
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />

                    <button
                        onClick={handleSendMessage}
                        disabled={!inputMessage.trim()}
                        className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </div>
            </div>

            {/* Upload indicator */}
            {isUploading && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white p-6 rounded-lg">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
                        <p className="mt-4 text-gray-700">Subiendo archivo...</p>
                    </div>
                </div>
            )}
        </div>
    );
}

export default App;